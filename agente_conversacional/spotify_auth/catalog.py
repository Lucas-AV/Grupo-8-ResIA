"""Cliente fino para os recursos Spotify usados pela central do produto.

Mantém chamadas à Web API fora das rotas e nunca expõe access tokens ao browser.
"""
from __future__ import annotations

from typing import Any

import requests

from spotify_auth.errors import SpotifyPlaylistError

API_BASE = "https://api.spotify.com/v1"


def call(access_token: str, path: str, *, method: str = "GET", params: dict[str, Any] | None = None,
         body: dict[str, Any] | None = None, timeout: float = 12) -> dict[str, Any]:
    try:
        response = requests.request(
            method, f"{API_BASE}{path}", headers={"Authorization": f"Bearer {access_token}"},
            params=params, json=body, timeout=timeout,
        )
    except requests.RequestException as exc:
        raise SpotifyPlaylistError("não foi possível comunicar com o Spotify") from exc
    if response.status_code == 204:
        return {"ok": True}
    try:
        payload = response.json()
    except ValueError as exc:
        raise SpotifyPlaylistError("Spotify respondeu um formato inválido") from exc
    if not response.ok:
        message = (payload.get("error") or {}).get("message", "falha na API Spotify")
        raise SpotifyPlaylistError(f"Spotify respondeu HTTP {response.status_code}: {message}")
    return payload


def spotify_path(value: str) -> str:
    """Evita path traversal e IDs inesperados vindos do browser."""
    if not value or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for ch in value):
        raise ValueError("identificador Spotify inválido")
    return value
