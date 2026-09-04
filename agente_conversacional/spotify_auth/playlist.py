import logging

import requests

from spotify_auth.errors import SpotifyPlaylistError

logger = logging.getLogger("agente.spotify_playlist")

_BASE_URL = "https://api.spotify.com/v1"
# Limite da Spotify Web API: no maximo 100 URIs por chamada a POST
# /playlists/{id}/tracks.
_MAX_URIS_POR_REQUISICAO = 100

_NOME_PADRAO = "Recomendacoes ResIA"
_DESCRICAO_PADRAO = "Playlist gerada pelo agente conversacional do Grupo 8 ResIA."


def _headers(access_token):
    return {"Authorization": f"Bearer {access_token}"}


def get_current_user_id(access_token, timeout=None):
    """GET /me — resolve o user_id do dono do access_token (ticket 12.1).

    spotify_auth/token_store.py so guarda access_token/refresh_token, nao o
    user_id — precisamos dele pra chamar POST /users/{user_id}/playlists,
    entao essa chamada extra e necessaria antes de criar a playlist.
    """
    try:
        response = requests.get(f"{_BASE_URL}/me", headers=_headers(access_token), timeout=timeout)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
        raise SpotifyPlaylistError(f"falha de rede ao chamar {_BASE_URL}/me: {exc}") from exc

    if response.status_code != 200:
        raise SpotifyPlaylistError(f"Spotify respondeu HTTP {response.status_code} em GET /me")

    try:
        body = response.json()
    except ValueError as exc:
        raise SpotifyPlaylistError("resposta do Spotify nao e JSON valido em GET /me") from exc

    user_id = body.get("id")
    if not user_id:
        raise SpotifyPlaylistError("resposta do Spotify em GET /me nao trouxe o campo 'id'")
    return user_id


def create_playlist(access_token, user_id, nome, descricao="", publica=False, timeout=None):
    """POST /users/{user_id}/playlists — cria a playlist vazia (ticket 12.1)."""
    try:
        response = requests.post(
            f"{_BASE_URL}/users/{user_id}/playlists",
            headers={**_headers(access_token), "Content-Type": "application/json"},
            json={"name": nome, "description": descricao, "public": publica},
            timeout=timeout,
        )
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
        raise SpotifyPlaylistError(f"falha de rede ao criar playlist: {exc}") from exc

    if response.status_code not in (200, 201):
        raise SpotifyPlaylistError(f"Spotify respondeu HTTP {response.status_code} ao criar a playlist")

    try:
        body = response.json()
    except ValueError as exc:
        raise SpotifyPlaylistError("resposta do Spotify nao e JSON valido ao criar a playlist") from exc

    playlist_id = body.get("id")
    if not playlist_id:
        raise SpotifyPlaylistError("resposta do Spotify ao criar a playlist nao trouxe o campo 'id'")

    return {
        "playlist_id": playlist_id,
        "url": (body.get("external_urls") or {}).get("spotify"),
    }


def add_tracks(access_token, playlist_id, track_ids, timeout=None):
    """POST /playlists/{playlist_id}/tracks — adiciona as faixas recomendadas,
    em lotes de ate 100 URIs por chamada (limite da Spotify Web API). Devolve
    quantas faixas foram efetivamente adicionadas.
    """
    uris = [f"spotify:track:{track_id}" for track_id in track_ids]
    total_adicionadas = 0

    for inicio in range(0, len(uris), _MAX_URIS_POR_REQUISICAO):
        lote = uris[inicio : inicio + _MAX_URIS_POR_REQUISICAO]
        try:
            response = requests.post(
                f"{_BASE_URL}/playlists/{playlist_id}/tracks",
                headers={**_headers(access_token), "Content-Type": "application/json"},
                json={"uris": lote},
                timeout=timeout,
            )
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
            raise SpotifyPlaylistError(f"falha de rede ao adicionar faixas na playlist: {exc}") from exc

        if response.status_code not in (200, 201):
            raise SpotifyPlaylistError(f"Spotify respondeu HTTP {response.status_code} ao adicionar faixas na playlist")

        total_adicionadas += len(lote)

    return total_adicionadas


def create_playlist_with_tracks(access_token, track_ids, nome=None, descricao=None, timeout=None):
    """Orquestra o fluxo completo do ticket 12.1: resolve o user_id logado,
    cria a playlist vazia e adiciona as faixas recomendadas nela.

    Propaga `SpotifyPlaylistError` pro chamador — a rota HTTP (ver
    spotify_auth/routes.py) e quem decide o status code de resposta, mesma
    convencao de spotify_auth/app_client.py.
    """
    user_id = get_current_user_id(access_token, timeout=timeout)
    playlist = create_playlist(
        access_token,
        user_id,
        nome or _NOME_PADRAO,
        descricao if descricao is not None else _DESCRICAO_PADRAO,
        timeout=timeout,
    )

    faixas_adicionadas = 0
    if track_ids:
        faixas_adicionadas = add_tracks(access_token, playlist["playlist_id"], track_ids, timeout=timeout)

    return {
        "playlist_id": playlist["playlist_id"],
        "url": playlist["url"],
        "faixas_adicionadas": faixas_adicionadas,
    }
