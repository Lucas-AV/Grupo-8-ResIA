import base64
import secrets
import time
from urllib.parse import urlencode

import requests
from flask import session

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
SCOPES = "user-top-read user-library-read user-read-recently-played"


class NotLoggedInError(Exception):
    pass


class CodeExchangeError(ValueError):
    def __init__(self, body, status_code):
        super().__init__(f"troca de code falhou com status {status_code}")
        self.body = body
        self.status_code = status_code


def get_login_url(client_id, redirect_uri):
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": SCOPES,
        "state": state,
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def _basic_auth_header(client_id, client_secret):
    credentials = f"{client_id}:{client_secret}".encode("utf-8")
    return base64.b64encode(credentials).decode("utf-8")


def exchange_code(code, state, client_id, client_secret, redirect_uri):
    if state != session.get("oauth_state"):
        raise ValueError("state inválido — possível CSRF, tente logar novamente")

    response = requests.post(
        TOKEN_URL,
        headers={"Authorization": f"Basic {_basic_auth_header(client_id, client_secret)}"},
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        },
    )
    if response.status_code != 200:
        raise CodeExchangeError(response.json(), response.status_code)

    payload = response.json()
    session["user_access_token"] = payload["access_token"]
    session["user_refresh_token"] = payload["refresh_token"]
    session["user_token_expires_at"] = time.time() + payload["expires_in"] - 30


def get_valid_user_token(client_id, client_secret):
    if "user_access_token" not in session:
        raise NotLoggedInError("faça login primeiro em /login")

    if session["user_token_expires_at"] > time.time():
        return session["user_access_token"]

    response = requests.post(
        TOKEN_URL,
        headers={"Authorization": f"Basic {_basic_auth_header(client_id, client_secret)}"},
        data={
            "grant_type": "refresh_token",
            "refresh_token": session["user_refresh_token"],
        },
    )
    if response.status_code != 200:
        session.clear()
        raise NotLoggedInError("sessão expirada, faça login novamente")

    payload = response.json()
    session["user_access_token"] = payload["access_token"]
    session["user_token_expires_at"] = time.time() + payload["expires_in"] - 30
    if "refresh_token" in payload:
        session["user_refresh_token"] = payload["refresh_token"]
    return session["user_access_token"]


def logout():
    session.clear()
