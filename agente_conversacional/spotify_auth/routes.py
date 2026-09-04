import logging
import time
import uuid
from typing import Optional

import segno
from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

from spotify_auth.client import PendingAuth, build_authorize_url, exchange_code_for_tokens, get_valid_access_token
from spotify_auth.consent import render_consent_page
from spotify_auth.errors import SpotifyNotAuthenticatedError, SpotifyPlaylistError, SpotifyTokenExchangeError
from spotify_auth.pairing_store import PairingStore
from spotify_auth.playlist import create_playlist_with_tracks
from spotify_auth.token_store import TokenStore
from spotify_auth.history import fetch_recently_played, fetch_saved_tracks, fetch_top_tracks
from recomendacao.historico_match import casar_historico_com_dataset
from recomendacao.perfil import calcular_perfil_usuario
from sessions.store import SessionNotFound

logger = logging.getLogger("agente.spotify_auth")

router = APIRouter()
_pending_auth = PendingAuth()
_pairing_store = PairingStore()
_token_store = None

_PAIRING_SUCCESS_PAGE = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>Spotify conectado</title></head>
<body><h1>Spotify conectado!</h1><p>Pode voltar pro outro dispositivo — já pode fechar essa aba.</p></body></html>"""

_PAIRING_EXPIRED_PAGE = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>QR code expirado</title></head>
<body><h1>Esse QR code expirou</h1><p>Volte pro outro dispositivo e gere um novo QR code.</p></body></html>"""


class CriarPlaylistRequest(BaseModel):
    """Corpo do POST /playlist/criar (ticket 12.1)."""

    session_id: str = Field(min_length=1)
    faixas: list[str] = Field(min_length=1, description="track_ids do Spotify a adicionar na playlist")
    nome: Optional[str] = None
    descricao: Optional[str] = None


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


@router.get("/auth/login")
def login(session_id: str = Query(...)):
    """Aviso de consentimento (ticket 5.10) antes do redirect real pro Spotify."""
    return HTMLResponse(render_consent_page(session_id))


@router.get("/auth/login/start")
def login_start(session_id: str = Query(...), pair: Optional[str] = Query(None)):
    """`pair` (opcional, ticket 13.13): quando presente, veio de um QR code de
    pareamento — o callback vai relayar os tokens pro código em vez de (só)
    salvar na sessão que de fato completou o OAuth (ver `/auth/qr`)."""
    return RedirectResponse(build_authorize_url(session_id, _pending_auth, pair_code=pair))


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

    pair_code = pending.get("pair_code")
    if pair_code:
        # Ticket 13.13: quem completou o OAuth foi o celular que escaneou o QR —
        # essa sessao (`pending["session_id"]`) e descartavel, os tokens de
        # verdade vao pro relay efemero pra o dispositivo que gerou o QR
        # (kiosk) consumir via /auth/pair/{code}/status.
        relayed = _pairing_store.mark_completed(pair_code, dict(tokens))
        if not relayed:
            logger.info("codigo de pareamento '%s' expirou antes do OAuth terminar", pair_code)
            return HTMLResponse(_PAIRING_EXPIRED_PAGE, status_code=410)
        return HTMLResponse(_PAIRING_SUCCESS_PAGE)

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


@router.get("/auth/qr")
def auth_qr(request: Request, session_id: str = Query(...)):
    """Ticket 13.13: gera um QR code de pareamento — o dispositivo que chama
    essa rota (kiosk) mostra o QR, outro dispositivo (celular) escaneia,
    autoriza a própria conta Spotify, e o kiosk recebe os tokens via polling
    em `/auth/pair/{code}/status`. Porta `spotify_explorer/app.py` (`/login/qr`
    + `pairing_store.py`) — nunca implementar esse fluxo em
    `spotify_explorer/frontend/`, aquilo é a ferramenta de dev."""
    code = _pairing_store.create()
    phone_session_id = f"qr-pair-{uuid.uuid4().hex}"
    pair_login_url = str(
        request.url_for("login_start").include_query_params(session_id=phone_session_id, pair=code)
    )
    qr_svg_data_uri = segno.make(pair_login_url).svg_data_uri(scale=6)
    return {
        "code": code,
        "qr_svg_data_uri": qr_svg_data_uri,
        "pair_login_url": pair_login_url,
        "expira_em_segundos": 300,
    }


@router.get("/auth/pair/{code}/status")
def auth_pair_status(code: str, request: Request, session_id: str = Query(...)):
    """Ticket 13.13: o kiosk faz polling nessa rota até `status == "completed"` —
    nesse ponto os tokens já foram salvos na sessão do kiosk (`session_id`,
    a mesma passada em `/auth/qr`), igual a um login normal via `/auth/callback`."""
    status_str, tokens = _pairing_store.consume_if_completed(code)
    if status_str == "completed":
        expires_at = time.time() + tokens["expires_in"]
        _get_token_store().save(session_id, tokens["access_token"], tokens["refresh_token"], expires_at)
        session_store = getattr(request.app.state, "session_store", None)
        if session_store is not None:
            try:
                session_store.mark_authenticated(session_id)
            except SessionNotFound:
                logger.info("sessao de chat nao existe mais; tokens OAuth permanecem armazenados")
    return {"status": status_str}


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

