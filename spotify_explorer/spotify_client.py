import base64
import time

import requests

TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"

_token_cache = {"access_token": None, "expires_at": 0}


class AppTokenError(Exception):
    def __init__(self, body, status_code):
        super().__init__(f"Spotify token request failed with status {status_code}")
        self.body = body
        self.status_code = status_code


def get_app_token(client_id, client_secret):
    if _token_cache["access_token"] and _token_cache["expires_at"] > time.time():
        return _token_cache["access_token"]

    credentials = f"{client_id}:{client_secret}".encode("utf-8")
    encoded = base64.b64encode(credentials).decode("utf-8")
    try:
        response = requests.post(
            TOKEN_URL,
            headers={"Authorization": f"Basic {encoded}"},
            data={"grant_type": "client_credentials"},
        )
    except requests.exceptions.RequestException as exc:
        raise AppTokenError({"error": "connection_error", "error_description": str(exc)}, 502)

    if response.status_code != 200:
        try:
            error_body = response.json()
        except ValueError:
            error_body = {
                "error": "invalid_response",
                "error_description": "resposta do token endpoint não é JSON",
            }
        raise AppTokenError(error_body, response.status_code)

    try:
        payload = response.json()
    except ValueError:
        raise AppTokenError(
            {
                "error": "invalid_response",
                "error_description": "resposta do token endpoint não é JSON",
            },
            response.status_code,
        )

    _token_cache["access_token"] = payload["access_token"]
    _token_cache["expires_at"] = time.time() + payload["expires_in"] - 30
    return _token_cache["access_token"]


def call_api(path, token, params=None, method="GET", json_body=None):
    try:
        if method == "GET":
            response = requests.get(
                f"{API_BASE}{path}",
                headers={"Authorization": f"Bearer {token}"},
                params=params or {},
            )
        else:
            response = requests.request(
                method,
                f"{API_BASE}{path}",
                headers={"Authorization": f"Bearer {token}"},
                params=params or {},
                json=json_body,
            )
    except requests.exceptions.RequestException as exc:
        return {"error": "connection_error", "error_description": str(exc)}, 502

    if response.status_code == 204:
        return {}, 204

    try:
        body = response.json()
    except ValueError:
        return (
            {"error": "invalid_response", "error_description": "resposta da Spotify não é JSON"},
            response.status_code,
        )

    retry_after = response.headers.get("Retry-After")
    if response.status_code == 429 and retry_after is not None:
        body["retry_after_seconds"] = retry_after
    return body, response.status_code


def api_get(path, client_id, client_secret, params=None):
    try:
        token = get_app_token(client_id, client_secret)
    except AppTokenError as exc:
        return exc.body, exc.status_code
    return call_api(path, token, params=params)
