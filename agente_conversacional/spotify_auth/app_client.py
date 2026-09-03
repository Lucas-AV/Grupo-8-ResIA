import base64
import time

import requests

from spotify_auth import config

API_BASE = "https://api.spotify.com/v1"
_DEFAULT_TIMEOUT_SEGUNDOS = 5
_MARGEM_EXPIRACAO_SEGUNDOS = 30

# Cache em memoria de processo do token de app — mesmo padrao de
# spotify_explorer/spotify_client.py (get_app_token), so que aqui reaproveita
# spotify_auth/config.py (client_id/client_secret/TOKEN_URL) em vez de
# duplicar a leitura de env vars.
_app_token_cache = {"access_token": None, "expires_at": 0.0}


def get_app_access_token(timeout=None):
    """Client Credentials Flow (ticket KAN-95) — token de aplicativo, sem
    login/sessao de usuario. So serve pra ler endpoints publicos como
    `GET /search`; nao tem escopo pra dados de usuario (isso continua sendo
    o fluxo PKCE de spotify_auth/client.py).

    Propaga qualquer erro (credenciais ausentes, rede, HTTP != 200, corpo
    nao-JSON) pro chamador — quem decide degradar graciosamente e
    `recomendacao/spotify_fallback.py`, nao este modulo."""
    if _app_token_cache["access_token"] and _app_token_cache["expires_at"] > time.time():
        return _app_token_cache["access_token"]

    credenciais = base64.b64encode(f"{config.client_id()}:{config.client_secret()}".encode("utf-8")).decode("utf-8")

    response = requests.post(
        config.TOKEN_URL,
        headers={"Authorization": f"Basic {credenciais}"},
        data={"grant_type": "client_credentials"},
        timeout=timeout or _DEFAULT_TIMEOUT_SEGUNDOS,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Spotify respondeu HTTP {response.status_code} em {config.TOKEN_URL}")

    payload = response.json()
    _app_token_cache["access_token"] = payload["access_token"]
    _app_token_cache["expires_at"] = time.time() + payload["expires_in"] - _MARGEM_EXPIRACAO_SEGUNDOS
    return _app_token_cache["access_token"]


def search_tracks(query, limit=10, timeout=None):
    """`GET /search?type=track` — devolve a lista bruta de objetos `track`
    do Spotify, ja na ordem de relevancia deles (nao reordenamos: sem audio
    features normalizadas pra essas faixas, ver
    recomendacao/spotify_fallback.py). Propaga excecoes, mesma convencao de
    `get_app_access_token`."""
    token = get_app_access_token(timeout=timeout)
    response = requests.get(
        f"{API_BASE}/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": query, "type": "track", "limit": max(1, min(50, limit))},
        timeout=timeout or _DEFAULT_TIMEOUT_SEGUNDOS,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Spotify respondeu HTTP {response.status_code} em {API_BASE}/search")

    body = response.json()
    return body.get("tracks", {}).get("items", []) or []


def get_tracks(track_ids, timeout=None):
    """`GET /tracks?ids=...` — devolve os objetos `track` brutos da Spotify
    pros ids pedidos (inclui `preview_url`), pra enriquecer faixas do
    dataset local (KAN-77), que só tem audio features, nunca preview. O
    endpoint aceita ate 50 ids por chamada; ids alem disso viram lotes
    adicionais (`GET /tracks` sucessivos) — hoje quem chama
    (`recomendacao/busca.py`) nunca manda mais que 30 ids (mesmo teto de
    `_validar_n_resultados`), entao na pratica isso e sempre uma unica
    chamada HTTP por resposta. Ids falsy (None/"") sao descartados antes
    de montar os lotes; lista de entrada vazia/só-de-falsy devolve `[]`
    sem chamar a Spotify.

    Propaga qualquer excecao, mesma convencao de `search_tracks` — quem
    decide degradar graciosamente e `recomendacao/busca.py`, nao este
    modulo."""
    ids_validos = [track_id for track_id in track_ids if track_id]
    if not ids_validos:
        return []

    token = get_app_access_token(timeout=timeout)
    faixas = []
    for inicio in range(0, len(ids_validos), 50):
        lote = ids_validos[inicio : inicio + 50]
        response = requests.get(
            f"{API_BASE}/tracks",
            headers={"Authorization": f"Bearer {token}"},
            params={"ids": ",".join(lote)},
            timeout=timeout or _DEFAULT_TIMEOUT_SEGUNDOS,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Spotify respondeu HTTP {response.status_code} em {API_BASE}/tracks")

        body = response.json()
        faixas.extend(body.get("tracks", []) or [])

    return faixas
