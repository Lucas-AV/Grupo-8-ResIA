import logging

import requests

logger = logging.getLogger("agente.spotify_history")

_BASE_URL = "https://api.spotify.com/v1"
_MAX_PAGINAS_SAVED_TRACKS = 20


def _request(url, access_token, timeout=None):
    try:
        response = requests.get(url, headers={"Authorization": f"Bearer {access_token}"}, timeout=timeout)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
        logger.warning("timeout/erro de rede ao chamar %s: %s — seguindo com historico parcial", url, exc)
        return None

    if response.status_code == 429:
        logger.warning(
            "rate limit (429) ao chamar %s (retry-after=%s) — seguindo com historico parcial",
            url,
            response.headers.get("Retry-After"),
        )
        return None

    if response.status_code != 200:
        logger.warning("Spotify respondeu HTTP %s em %s — seguindo com historico parcial", response.status_code, url)
        return None

    return response.json()


def fetch_top_tracks(access_token, timeout=None):
    """GET /me/top/tracks — janela de ~6 meses (ticket 5.5)."""
    body = _request(f"{_BASE_URL}/me/top/tracks?time_range=medium_term", access_token, timeout)
    return (body or {}).get("items", [])


def fetch_recently_played(access_token, timeout=None):
    """GET /me/player/recently-played — ultimas faixas tocadas (ticket 5.5)."""
    body = _request(f"{_BASE_URL}/me/player/recently-played?limit=50", access_token, timeout)
    return (body or {}).get("items", [])


def fetch_saved_tracks(access_token, timeout=None):
    """GET /me/tracks, paginado — faixas curtidas pelo usuario (ticket 5.5)."""
    faixas = []
    url = f"{_BASE_URL}/me/tracks?limit=50"
    paginas = 0
    while url and paginas < _MAX_PAGINAS_SAVED_TRACKS:
        body = _request(url, access_token, timeout)
        if body is None:
            break
        faixas.extend(body.get("items", []))
        url = body.get("next")
        paginas += 1
    return faixas
