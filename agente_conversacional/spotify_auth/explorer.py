"""Chamadas de leitura/controle da Spotify Web API com o token do usuário logado (Épico 13).

Porta pra dentro do produto real o que o spotify_explorer (ferramenta de dev,
ver `spotify_explorer/app.py` + `spotify_client.py`) já fazia com client-credentials
ou com o token do dev tool — aqui tudo usa o access_token PKCE da própria sessão
de chat (`spotify_auth/client.py`), já que os endpoints de catálogo do Spotify
aceitam qualquer Bearer token válido, sem exigir escopo extra.
"""

import logging

import requests

from spotify_auth.errors import SpotifyExplorerError

logger = logging.getLogger("agente.spotify_explorer")

_BASE_URL = "https://api.spotify.com/v1"


def _headers(access_token):
    return {"Authorization": f"Bearer {access_token}"}


def _request(method, path, access_token, params=None, json_body=None, timeout=None):
    try:
        response = requests.request(
            method,
            f"{_BASE_URL}{path}",
            headers=_headers(access_token),
            params=params,
            json=json_body,
            timeout=timeout,
        )
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
        raise SpotifyExplorerError(f"falha de rede ao chamar {method} {path}: {exc}") from exc

    if response.status_code >= 400:
        raise SpotifyExplorerError(
            f"Spotify respondeu HTTP {response.status_code} em {method} {path}",
            status_code=response.status_code,
        )

    if response.status_code == 204 or not response.content:
        return {}

    try:
        return response.json()
    except ValueError as exc:
        raise SpotifyExplorerError(f"resposta do Spotify nao e JSON valido em {method} {path}") from exc


# --- Catálogo (busca, faixa, artista, álbum, playlist, lançamentos) — 13.1-13.5, 13.7 ---


def search(access_token, query, tipo="track", limit=10, timeout=None):
    return _request("GET", "/search", access_token, params={"q": query, "type": tipo, "limit": limit}, timeout=timeout)


def get_track(access_token, track_id, timeout=None):
    return _request("GET", f"/tracks/{track_id}", access_token, timeout=timeout)


def get_audio_features(access_token, track_id, timeout=None):
    return _request("GET", f"/audio-features/{track_id}", access_token, timeout=timeout)


def get_audio_analysis(access_token, track_id, timeout=None):
    return _request("GET", f"/audio-analysis/{track_id}", access_token, timeout=timeout)


def get_artist(access_token, artist_id, timeout=None):
    return _request("GET", f"/artists/{artist_id}", access_token, timeout=timeout)


def get_artist_top_tracks(access_token, artist_id, market="US", timeout=None):
    return _request(
        "GET", f"/artists/{artist_id}/top-tracks", access_token, params={"market": market}, timeout=timeout
    )


def get_artist_albums(access_token, artist_id, timeout=None):
    return _request("GET", f"/artists/{artist_id}/albums", access_token, timeout=timeout)


def get_related_artists(access_token, artist_id, timeout=None):
    return _request("GET", f"/artists/{artist_id}/related-artists", access_token, timeout=timeout)


def get_album(access_token, album_id, timeout=None):
    return _request("GET", f"/albums/{album_id}", access_token, timeout=timeout)


def get_playlist(access_token, playlist_id, timeout=None):
    return _request("GET", f"/playlists/{playlist_id}", access_token, timeout=timeout)


def get_new_releases(access_token, limit=20, timeout=None):
    return _request("GET", "/browse/new-releases", access_token, params={"limit": limit}, timeout=timeout)


def get_recommendations(access_token, params, timeout=None):
    """`params` é repassado direto pra query string (`seed_tracks`/`seed_artists`/`seed_genres`/`limit`/etc — 13.8)."""
    return _request("GET", "/recommendations", access_token, params=params, timeout=timeout)


# --- Dados do usuário logado — 13.6, 13.9, 13.10 ---


def get_me(access_token, timeout=None):
    return _request("GET", "/me", access_token, timeout=timeout)


def get_my_top_tracks(access_token, time_range="medium_term", limit=20, timeout=None):
    return _request(
        "GET", "/me/top/tracks", access_token, params={"time_range": time_range, "limit": limit}, timeout=timeout
    )


def get_my_top_artists(access_token, time_range="medium_term", limit=20, timeout=None):
    return _request(
        "GET", "/me/top/artists", access_token, params={"time_range": time_range, "limit": limit}, timeout=timeout
    )


def get_my_saved_tracks(access_token, limit=20, offset=0, timeout=None):
    return _request("GET", "/me/tracks", access_token, params={"limit": limit, "offset": offset}, timeout=timeout)


def get_recently_played(access_token, limit=20, timeout=None):
    return _request("GET", "/me/player/recently-played", access_token, params={"limit": limit}, timeout=timeout)


def get_my_following(access_token, limit=20, timeout=None):
    return _request(
        "GET", "/me/following", access_token, params={"type": "artist", "limit": limit}, timeout=timeout
    )


def get_my_playlists(access_token, limit=20, offset=0, timeout=None):
    return _request("GET", "/me/playlists", access_token, params={"limit": limit, "offset": offset}, timeout=timeout)


# --- Controles de reprodução (Spotify Connect) — 13.11 ---


def get_player_state(access_token, timeout=None):
    return _request("GET", "/me/player", access_token, timeout=timeout)


def get_player_queue(access_token, timeout=None):
    return _request("GET", "/me/player/queue", access_token, timeout=timeout)


def player_play(access_token, timeout=None):
    return _request("PUT", "/me/player/play", access_token, timeout=timeout)


def play_track(access_token, track_uri, device_id=None, timeout=None):
    """Toca uma faixa especifica no dispositivo Spotify Connect ativo do
    usuario (ticket 13.14) — diferente de `player_play` (retoma o que ja
    estava tocando), aqui trocamos o conteudo pra `track_uri`
    (`spotify:track:{id}`). `device_id` opcional mira um dispositivo
    especifico (varios ativos); sem ele, a Spotify usa o dispositivo ativo
    mais recente. HTTP 404 da Spotify aqui normalmente significa "nenhum
    dispositivo ativo" — quem chama decide como comunicar isso."""
    params = {"device_id": device_id} if device_id else None
    return _request(
        "PUT", "/me/player/play", access_token, params=params, json_body={"uris": [track_uri]}, timeout=timeout
    )


def player_pause(access_token, timeout=None):
    return _request("PUT", "/me/player/pause", access_token, timeout=timeout)


def player_next(access_token, timeout=None):
    return _request("POST", "/me/player/next", access_token, timeout=timeout)


def player_previous(access_token, timeout=None):
    return _request("POST", "/me/player/previous", access_token, timeout=timeout)


def player_seek(access_token, position_ms, timeout=None):
    return _request("PUT", "/me/player/seek", access_token, params={"position_ms": position_ms}, timeout=timeout)


def player_set_volume(access_token, volume_percent, timeout=None):
    return _request(
        "PUT", "/me/player/volume", access_token, params={"volume_percent": volume_percent}, timeout=timeout
    )


def player_set_shuffle(access_token, state, timeout=None):
    return _request("PUT", "/me/player/shuffle", access_token, params={"state": state}, timeout=timeout)


def player_set_repeat(access_token, state, timeout=None):
    return _request("PUT", "/me/player/repeat", access_token, params={"state": state}, timeout=timeout)


# --- Biblioteca do usuário — salvar faixa (ticket 13.15) ---


def save_track(access_token, track_id, timeout=None):
    """PUT /me/tracks — salva a faixa em "Músicas Curtidas" da conta
    logada. Idempotente do lado da Spotify (salvar uma faixa já salva não
    dá erro), então não precisa checar o estado atual antes de chamar."""
    return _request("PUT", "/me/tracks", access_token, params={"ids": track_id}, timeout=timeout)
