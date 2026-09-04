"""Busca de video_id no YouTube como prévia de áudio (ticket 13.12 / KAN-121).

Contorna a restrição da Spotify: `preview_url` vem `null` pra apps criados
apos nov/2024 (ver docs/superpowers/specs/2026-09-03-spotify-preview-player-design.md),
entao o frontend nao tem de onde tocar um clipe curto da faixa recomendada.
Aqui buscamos o video correspondente no YouTube e devolvemos so o `video_id`
— o frontend toca via YouTube IFrame Player API embutido, sem extrair stream
de audio (uso oficial do player, dentro dos termos do YouTube)."""

import os

import requests

_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
_TIMEOUT_SEGUNDOS = 5

# Cache em nivel de modulo (mesmo padrao de app_client._app_token_cache):
# evita reconsultar a mesma faixa a cada card renderizado, importante dado o
# quota diario limitado da YouTube Data API (100 unidades por busca).
_video_id_cache: dict[str, str | None] = {}


def buscar_video_id(nome, artista, timeout=None):
    """Devolve o `video_id` do resultado mais relevante pra "<nome> <artista>",
    ou None se a chave nao estiver configurada, a busca nao achar nada, ou
    qualquer falha (rede, HTTP, corpo inesperado) acontecer — nunca levanta
    excecao, mesma filosofia defensiva de `recomendacao/spotify_fallback.py`."""
    if not nome:
        return None

    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        return None

    consulta = f"{nome} {artista}".strip() if artista else nome
    chave_cache = consulta.lower()
    if chave_cache in _video_id_cache:
        return _video_id_cache[chave_cache]

    video_id = _consultar_youtube(consulta, api_key, timeout)
    _video_id_cache[chave_cache] = video_id
    return video_id


def _consultar_youtube(consulta, api_key, timeout):
    try:
        resposta = requests.get(
            _SEARCH_URL,
            params={
                "part": "snippet",
                "q": consulta,
                "type": "video",
                "maxResults": 1,
                "key": api_key,
            },
            timeout=timeout or _TIMEOUT_SEGUNDOS,
        )
    except Exception:
        return None

    if resposta.status_code != 200:
        return None

    try:
        itens = resposta.json().get("items") or []
    except Exception:
        return None

    if not itens:
        return None

    return itens[0].get("id", {}).get("videoId")
