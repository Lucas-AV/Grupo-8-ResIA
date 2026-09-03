import logging
import time
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import RedirectResponse

from spotify_auth.client import PendingAuth, build_authorize_url, exchange_code_for_tokens
from spotify_auth.errors import SpotifyTokenExchangeError
from spotify_auth.token_store import TokenStore

logger = logging.getLogger("agente.spotify_auth")

router = APIRouter()
_pending_auth = PendingAuth()
_token_store = None


def _get_token_store():
    global _token_store
    if _token_store is None:
        _token_store = TokenStore()
    return _token_store


@router.get("/auth/login")
def login(session_id: str = Query(...)):
    return RedirectResponse(build_authorize_url(session_id, _pending_auth))


@router.get("/auth/callback")
def callback(code: Optional[str] = None, state: Optional[str] = None, error: Optional[str] = None):
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
    return RedirectResponse("/?spotify_login=success")


@router.post("/auth/logout")
def logout(session_id: str = Query(...)):
    _get_token_store().delete(session_id)
    return {"status": "logged_out"}
