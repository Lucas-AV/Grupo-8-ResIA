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
from spotify_auth.token_store import TokenStore
from sessions.store import SessionNotFound

logger = logging.getLogger("agente.spotify_auth")

router = APIRouter()
_pending_auth = PendingAuth()
_token_store = None


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

    expires_at = time.time() + tokens["expires_in"]
    _get_token_store().save(pending["session_id"], tokens["access_token"], tokens["refresh_token"], expires_at)
    session_store = getattr(request.app.state, "session_store", None)
    if session_store is not None:
        try:
            session_store.mark_authenticated(pending["session_id"])
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
