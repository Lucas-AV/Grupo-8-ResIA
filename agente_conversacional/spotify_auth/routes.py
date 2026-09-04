import logging
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

from spotify_auth.client import PendingAuth, build_authorize_url, exchange_code_for_tokens, get_valid_access_token
from spotify_auth.consent import render_consent_page
from spotify_auth.errors import SpotifyNotAuthenticatedError, SpotifyPlaylistError, SpotifyTokenExchangeError
from spotify_auth.playlist import create_playlist_with_tracks
from spotify_auth.catalog import call as spotify_call, spotify_path
from spotify_auth.pairing import PairingStore
from spotify_auth.token_store import TokenStore
from spotify_auth.history import fetch_recently_played, fetch_saved_tracks, fetch_top_tracks
from recomendacao.historico_match import casar_historico_com_dataset
from recomendacao.perfil import calcular_perfil_usuario
from sessions.store import SessionNotFound

logger = logging.getLogger("agente.spotify_auth")

router = APIRouter()
_pending_auth = PendingAuth()
_token_store = None
_pairing_store = PairingStore()


class CriarPlaylistRequest(BaseModel):
    """Corpo do POST /playlist/criar (ticket 12.1)."""

    session_id: str = Field(min_length=1)
    faixas: list[str] = Field(min_length=1, description="track_ids do Spotify a adicionar na playlist")
    nome: Optional[str] = None
    descricao: Optional[str] = None


class SpotifyCommand(BaseModel):
    session_id: str = Field(min_length=1)
    value: Optional[str] = None


class QrApproval(BaseModel):
    session_id: str = Field(min_length=1)


def _get_token_store():
    global _token_store
    if _token_store is None:
        _token_store = TokenStore()
    return _token_store


def _perfil_e_cobertura_do_historico(access_token):
    """Calcula o perfil e registra somente números agregados do matching.

    O log não contém token, sessão, nomes de faixas nem informações da conta.
    Falhas aqui nunca impedem a pessoa de concluir o login.
    """
    try:
        historico = [
            *fetch_top_tracks(access_token),
            *fetch_recently_played(access_token),
            *fetch_saved_tracks(access_token),
        ]
        cobertura = casar_historico_com_dataset(historico)
        perfil = calcular_perfil_usuario(historico)
        logger.info(
            "cobertura_matching_oauth=%.1f%% faixas_casadas=%d faixas_historico=%d",
            cobertura["taxa_cobertura"] * 100,
            cobertura["total_casadas"],
            cobertura["total_historico"],
        )
        return perfil
    except Exception:
        logger.warning("não foi possível calcular a cobertura do matching OAuth; seguindo sem perfil", exc_info=True)
        return None


def _spotify(session_id: str, path: str, *, method: str = "GET", params=None, body=None):
    """Executa uma chamada autenticada e normaliza erros sem vazar credenciais."""
    try:
        token = get_valid_access_token(session_id, _get_token_store())
        return spotify_call(token, path, method=method, params=params, body=body)
    except SpotifyNotAuthenticatedError:
        raise HTTPException(401, detail={"codigo": "spotify_nao_autenticado", "mensagem": "Conecte sua conta Spotify."})
    except (SpotifyPlaylistError, ValueError) as exc:
        logger.warning("falha Spotify em %s: %s", path, exc)
        raise HTTPException(502, detail={"codigo": "spotify_indisponivel", "mensagem": str(exc)})


@router.get("/auth/login")
def login(session_id: str = Query(...)):
    """Aviso de consentimento (ticket 5.10) antes do redirect real pro Spotify."""
    return HTMLResponse(render_consent_page(session_id))


@router.get("/auth/login/start")
def login_start(session_id: str = Query(...)):
    return RedirectResponse(build_authorize_url(session_id, _pending_auth))


@router.get("/auth/callback")
def callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    if error:
        logger.info("login Spotify cancelado pelo usuario (%s) — sessao permanece anonima", error)
        return RedirectResponse("/?spotify_login=cancelled")

    pending = _pending_auth.consume(state) if state else None
    if pending is None:
        logger.warning("callback do Spotify com 'state' invalido ou desconhecido (possivel CSRF)")
        return RedirectResponse("/?spotify_login=state_mismatch")

    try:
        tokens = exchange_code_for_tokens(code, pending["code_verifier"])
    except SpotifyTokenExchangeError as exc:
        logger.warning("falha ao trocar codigo por token: %s", exc)
        return RedirectResponse("/?spotify_login=failed")

    # No QR o celular só autoriza. O dispositivo que iniciou o fluxo precisa
    # aprovar a vinculação antes que os tokens sejam gravados.
    pair_code = pending.get("pair_code")
    if pair_code:
        pairing = _pairing_store.get(pair_code)
        if pairing is None:
            return HTMLResponse("<h1>Este QR expirou.</h1>", status_code=410)
        pairing.tokens = tokens
        return HTMLResponse("<h1>Spotify autorizado</h1><p>Volte ao dispositivo que exibiu o QR e confirme a vinculação.</p>")

    expires_at = time.time() + tokens["expires_in"]
    _get_token_store().save(pending["session_id"], tokens["access_token"], tokens["refresh_token"], expires_at)
    session_store = getattr(request.app.state, "session_store", None)
    if session_store is not None:
        try:
            session_store.mark_authenticated(
                pending["session_id"],
                _perfil_e_cobertura_do_historico(tokens["access_token"]),
            )
        except SessionNotFound:
            logger.info("sessao de chat nao existe mais; tokens OAuth permanecem armazenados")
    return RedirectResponse("/?spotify_login=success")


@router.post("/auth/qr")
def create_qr(request: Request, session_id: str = Query(...)):
    """Cria QR curto e de uso único; o SVG é gerado sem enviar dados a terceiros."""
    code, secret = _pairing_store.create(session_id)
    url = str(request.base_url).rstrip("/") + f"/auth/qr/{code}?secret={secret}"
    try:
        import segno
        qr_svg = segno.make(url).svg_inline(scale=4)
    except ImportError:  # permite boot explicando a dependência em vez de quebrar a API
        raise HTTPException(503, detail={"codigo": "qr_indisponivel", "mensagem": "Instale a dependência segno para habilitar QR."})
    return {"code": code, "url": url, "qr_svg": qr_svg, "expires_in": _pairing_store.ttl_seconds}


@router.get("/auth/qr/{code}")
def open_qr(code: str, secret: str = Query(...)):
    if _pairing_store.get(code, secret) is None:
        return HTMLResponse("<h1>QR inválido ou expirado.</h1>", status_code=410)
    return HTMLResponse(f'<h1>Conectar ao Spotify</h1><p>Autorize no Spotify e confirme no dispositivo original.</p><a href="/auth/qr/{code}/start?secret={secret}">Continuar</a>')


@router.get("/auth/qr/{code}/start")
def start_qr_login(code: str, secret: str = Query(...)):
    if _pairing_store.get(code, secret) is None:
        return HTMLResponse("<h1>QR inválido ou expirado.</h1>", status_code=410)
    return RedirectResponse(build_authorize_url(f"qr:{code}", _pending_auth, pair_code=code))


@router.get("/auth/qr/{code}/status")
def qr_status(code: str, session_id: str = Query(...)):
    pairing = _pairing_store.get(code)
    if pairing is None or pairing.session_id != session_id:
        raise HTTPException(404, detail={"codigo": "qr_nao_encontrado"})
    return {"status": "pending_approval" if pairing.tokens else "waiting"}


@router.post("/auth/qr/{code}/approve")
def approve_qr(code: str, body: QrApproval, request: Request):
    pairing = _pairing_store.consume(code)
    if pairing is None or pairing.session_id != body.session_id or not pairing.tokens:
        raise HTTPException(409, detail={"codigo": "qr_ainda_nao_autorizado"})
    tokens = pairing.tokens
    _get_token_store().save(pairing.session_id, tokens["access_token"], tokens["refresh_token"], time.time() + tokens["expires_in"])
    store = getattr(request.app.state, "session_store", None)
    if store:
        try: store.mark_authenticated(pairing.session_id, _perfil_e_cobertura_do_historico(tokens["access_token"]))
        except SessionNotFound: pass
    return {"status": "connected"}


@router.post("/auth/logout")
def logout(session_id: str = Query(...)):
    _get_token_store().delete(session_id)
    return {"status": "logged_out"}


@router.get("/auth/status")
def auth_status(session_id: str = Query(...)):
    """Ticket 12.2: o frontend usa isso pra saber se mostra acoes que exigem
    login com o Spotify (ex.: botao "Salvar no Spotify") sem precisar
    depender so do parametro `spotify_login` do redirect do callback."""
    return {"autenticado": _get_token_store().get(session_id) is not None}


@router.post("/playlist/criar")
def criar_playlist(body: CriarPlaylistRequest):
    """Ticket 12.1 (KAN-104): cria uma playlist de verdade na conta Spotify
    da sessao autenticada com as faixas recomendadas, usando o access_token
    valido de spotify_auth/client.py (ticket 5.4, renova sozinho quando
    necessario). Sessao sem login no Spotify nunca chega a tentar criar
    playlist nenhuma — falha cedo com 401 e um codigo de erro claro."""
    try:
        access_token = get_valid_access_token(body.session_id, _get_token_store())
    except SpotifyNotAuthenticatedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "codigo": "spotify_nao_autenticado",
                "mensagem": "Faça login com o Spotify antes de salvar uma playlist.",
            },
        )

    try:
        resultado = create_playlist_with_tracks(access_token, body.faixas, nome=body.nome, descricao=body.descricao)
    except SpotifyPlaylistError as exc:
        logger.warning("falha ao criar playlist no Spotify: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "codigo": "spotify_playlist_falhou",
                "mensagem": "Não foi possível criar a playlist no Spotify agora. Tente novamente em instantes.",
            },
        )

    return resultado


# Épico 13 — catálogo e dados do usuário. Todos os caminhos passam por _spotify:
# token por sessão, renovação centralizada e nenhum token no JavaScript.
@router.get("/spotify/search")
def spotify_search(session_id: str = Query(...), q: str = Query(..., min_length=1), type: str = Query("track"), limit: int = Query(10, ge=1, le=20)):
    allowed = {"track", "artist", "album", "playlist"}
    kinds = [item for item in type.split(",") if item in allowed]
    if not kinds:
        raise HTTPException(422, detail="type deve incluir track, artist, album ou playlist")
    return _spotify(session_id, "/search", params={"q": q, "type": ",".join(kinds), "limit": limit})


@router.get("/spotify/tracks/{track_id}")
def track_details(track_id: str, session_id: str = Query(...)):
    item = spotify_path(track_id)
    return {"track": _spotify(session_id, f"/tracks/{item}"), "audio_features": _spotify(session_id, f"/audio-features/{item}"), "audio_analysis": _spotify(session_id, f"/audio-analysis/{item}")}


@router.get("/spotify/artists/{artist_id}")
def artist_details(artist_id: str, session_id: str = Query(...), market: str = Query("BR", min_length=2, max_length=2)):
    item = spotify_path(artist_id)
    # related-artists foi removido da Web API em versões recentes; tratamos sua
    # ausência como capability, preservando perfil/top tracks/álbuns.
    related = None
    try: related = _spotify(session_id, f"/artists/{item}/related-artists")
    except HTTPException: related = {"artists": [], "unavailable": True}
    return {"artist": _spotify(session_id, f"/artists/{item}"), "top_tracks": _spotify(session_id, f"/artists/{item}/top-tracks", params={"market": market}), "albums": _spotify(session_id, f"/artists/{item}/albums", params={"limit": 20}), "related_artists": related}


@router.get("/spotify/albums/{album_id}")
def album_details(album_id: str, session_id: str = Query(...)):
    return _spotify(session_id, f"/albums/{spotify_path(album_id)}")


@router.get("/spotify/playlists/{playlist_id}")
def playlist_details(playlist_id: str, session_id: str = Query(...)):
    return _spotify(session_id, f"/playlists/{spotify_path(playlist_id)}")


@router.get("/spotify/me")
def spotify_me(session_id: str = Query(...)):
    return {
        "profile": _spotify(session_id, "/me"),
        "top_tracks": _spotify(session_id, "/me/top/tracks", params={"limit": 10}),
        "top_artists": _spotify(session_id, "/me/top/artists", params={"limit": 10}),
        "recently_played": _spotify(session_id, "/me/player/recently-played", params={"limit": 10}),
        "saved_tracks": _spotify(session_id, "/me/tracks", params={"limit": 10}),
    }


@router.get("/spotify/me/playlists")
def spotify_playlists(session_id: str = Query(...), limit: int = Query(20, ge=1, le=50)):
    return _spotify(session_id, "/me/playlists", params={"limit": limit})


@router.get("/spotify/me/following")
def spotify_following(session_id: str = Query(...), limit: int = Query(20, ge=1, le=50)):
    return _spotify(session_id, "/me/following", params={"type": "artist", "limit": limit})


@router.get("/spotify/new-releases")
def new_releases(session_id: str = Query(...), limit: int = Query(20, ge=1, le=50)):
    # browse/new-releases não está disponível para todos os apps novos. A
    # chamada continua encapsulada para retorno claro caso a capability falte.
    return _spotify(session_id, "/browse/new-releases", params={"limit": limit, "country": "BR"})


@router.get("/spotify/recommendations")
def native_recommendations(session_id: str = Query(...), seed_tracks: str | None = None, seed_artists: str | None = None, seed_genres: str | None = None):
    params = {key: value for key, value in {"seed_tracks": seed_tracks, "seed_artists": seed_artists, "seed_genres": seed_genres, "limit": 20}.items() if value}
    if not any(key.startswith("seed_") for key in params):
        raise HTTPException(422, detail="informe ao menos uma seed")
    return _spotify(session_id, "/recommendations", params=params)


@router.get("/spotify/player")
def get_player(session_id: str = Query(...)):
    return {"state": _spotify(session_id, "/me/player"), "queue": _spotify(session_id, "/me/player/queue")}


@router.post("/spotify/player/{action}")
def player_command(action: str, body: SpotifyCommand, state: str | None = Query(None), volume_percent: int | None = Query(None), position_ms: int | None = Query(None, ge=0)):
    paths = {"play": ("/me/player/play", "PUT"), "pause": ("/me/player/pause", "PUT"), "next": ("/me/player/next", "POST"), "previous": ("/me/player/previous", "POST"), "shuffle": ("/me/player/shuffle", "PUT"), "repeat": ("/me/player/repeat", "PUT"), "volume": ("/me/player/volume", "PUT"), "seek": ("/me/player/seek", "PUT"), "queue": ("/me/player/queue", "POST")}
    if action not in paths: raise HTTPException(404, detail="controle desconhecido")
    path, method = paths[action]
    params = {}
    if action in {"shuffle", "repeat"}: params["state"] = state or ("false" if action == "shuffle" else "off")
    if volume_percent is not None: params["volume_percent"] = volume_percent
    if action == "seek" and position_ms is None: raise HTTPException(422, detail="informe position_ms")
    if position_ms is not None: params["position_ms"] = position_ms
    if action == "queue":
        if not body.value: raise HTTPException(422, detail="informe a URI da faixa")
        params["uri"] = body.value
    return _spotify(body.session_id, path, method=method, params=params)
