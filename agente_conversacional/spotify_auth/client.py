import time
from urllib.parse import urlencode

import requests

from spotify_auth import config, pkce
from spotify_auth.errors import SpotifyNotAuthenticatedError, SpotifyTokenExchangeError

_REFRESH_MARGIN_SECONDS = 60


class PendingAuth:
    """Correlaciona o `state` do PKCE com code_verifier/session_id/redirect_uri
    entre /auth/login e /auth/callback (ticket 5.2). `redirect_uri` (ticket
    KAN-169) fica preso ao `state` porque o OAuth exige que o valor mandado
    na troca de codigo por token seja exatamente o mesmo usado no /authorize
    inicial — guardar aqui e o unico jeito de suportar varios dominios
    rodando ao mesmo tempo (LAN local + tunel publico) sem misturar um
    login com o redirect_uri de outro."""

    def __init__(self):
        self._pending = {}

    def start(self, session_id, redirect_uri, pair_code=None):
        state = pkce.generate_state()
        code_verifier = pkce.generate_code_verifier()
        self._pending[state] = {
            "session_id": session_id,
            "code_verifier": code_verifier,
            "redirect_uri": redirect_uri,
            "pair_code": pair_code,
        }
        return state, code_verifier

    def consume(self, state):
        return self._pending.pop(state, None)


def build_authorize_url(session_id, pending_auth, redirect_uri, pair_code=None):
    """`redirect_uri` (ticket KAN-169) vem de quem chamou — normalmente
    calculado a partir do Host da requisicao que bateu em /auth/login/start
    (ver spotify_auth/routes.py), nao de uma config fixa — assim o mesmo
    backend aceita login vindo de qualquer dominio que esteja cadastrado no
    Spotify Dashboard (LAN local, tunel publico, etc.), todos ao mesmo tempo."""
    state, code_verifier = pending_auth.start(session_id, redirect_uri, pair_code=pair_code)
    params = {
        "client_id": config.client_id(),
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": config.SCOPES,
        "state": state,
        "code_challenge_method": "S256",
        "code_challenge": pkce.generate_code_challenge(code_verifier),
    }
    return f"{config.AUTHORIZE_URL}?{urlencode(params)}"


def _post_token(data, timeout=None):
    try:
        response = requests.post(
            config.TOKEN_URL,
            data=data,
            auth=(config.client_id(), config.client_secret()),
            timeout=timeout,
        )
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
        raise SpotifyTokenExchangeError(f"falha de rede ao chamar {config.TOKEN_URL}: {exc}") from exc

    if response.status_code != 200:
        raise SpotifyTokenExchangeError(f"Spotify respondeu HTTP {response.status_code} em {config.TOKEN_URL}")

    try:
        return response.json()
    except ValueError as exc:
        raise SpotifyTokenExchangeError("resposta do Spotify nao e JSON valido") from exc


def exchange_code_for_tokens(code, code_verifier, redirect_uri, timeout=None):
    """`redirect_uri` tem que ser identico ao que foi mandado no /authorize
    original (ver PendingAuth) — o OAuth exige isso, a Spotify rejeita a
    troca se os dois valores nao baterem."""
    body = _post_token(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": config.client_id(),
            "code_verifier": code_verifier,
        },
        timeout=timeout,
    )
    return {
        "access_token": body["access_token"],
        "refresh_token": body["refresh_token"],
        "expires_in": body["expires_in"],
    }


def refresh_access_token(refresh_token, timeout=None):
    body = _post_token(
        {"grant_type": "refresh_token", "refresh_token": refresh_token, "client_id": config.client_id()},
        timeout=timeout,
    )
    return {
        "access_token": body["access_token"],
        "refresh_token": body.get("refresh_token", refresh_token),
        "expires_in": body["expires_in"],
    }


def get_valid_access_token(session_id, token_store, timeout=None):
    """Devolve um access_token valido, renovando proativamente se faltar menos de 60s (ticket 5.4)."""
    tokens = token_store.get(session_id)
    if tokens is None:
        raise SpotifyNotAuthenticatedError(session_id)

    if tokens["expires_at"] - time.time() > _REFRESH_MARGIN_SECONDS:
        return tokens["access_token"]

    try:
        refreshed = refresh_access_token(tokens["refresh_token"], timeout=timeout)
    except SpotifyTokenExchangeError as exc:
        # refresh_token invalido/revogado (ticket 3.7): sessao cai pra anonima, nao propaga o erro de rede.
        token_store.delete(session_id)
        raise SpotifyNotAuthenticatedError(session_id) from exc

    expires_at = time.time() + refreshed["expires_in"]
    token_store.save(session_id, refreshed["access_token"], refreshed["refresh_token"], expires_at)
    return refreshed["access_token"]
