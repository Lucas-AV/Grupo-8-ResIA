import base64
import time

import requests

TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"

_token_cache = {"access_token": None, "expires_at": 0}


def get_app_token(client_id, client_secret):
    if _token_cache["access_token"] and _token_cache["expires_at"] > time.time():
        return _token_cache["access_token"]

    credentials = f"{client_id}:{client_secret}".encode("utf-8")
    encoded = base64.b64encode(credentials).decode("utf-8")
    response = requests.post(
        TOKEN_URL,
        headers={"Authorization": f"Basic {encoded}"},
        data={"grant_type": "client_credentials"},
    )
    response.raise_for_status()
    payload = response.json()
    _token_cache["access_token"] = payload["access_token"]
    _token_cache["expires_at"] = time.time() + payload["expires_in"] - 30
    return _token_cache["access_token"]


def call_api(path, token, params=None):
    response = requests.get(
        f"{API_BASE}{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params or {},
    )
    body = response.json()
    retry_after = response.headers.get("Retry-After")
    if response.status_code == 429 and retry_after is not None:
        body["retry_after_seconds"] = retry_after
    return body, response.status_code


def api_get(path, client_id, client_secret, params=None):
    token = get_app_token(client_id, client_secret)
    return call_api(path, token, params=params)
