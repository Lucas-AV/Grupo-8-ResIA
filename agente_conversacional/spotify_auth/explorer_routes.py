"""Rotas HTTP do Épico 13 — integração das funcionalidades do spotify_explorer no produto.

Cada rota resolve o access_token válido da sessão (mesmo fluxo PKCE de
`spotify_auth/routes.py`) e delega a chamada de fato pra `spotify_auth/explorer.py`.
Nunca implementar essas telas em `spotify_explorer/frontend/` — aquilo é a
ferramenta de dev, este módulo é o produto real.
"""

import logging

from fastapi import APIRouter, HTTPException, Query, status

from spotify_auth import explorer
from spotify_auth.client import get_valid_access_token
from spotify_auth.errors import SpotifyExplorerError, SpotifyNotAuthenticatedError
from spotify_auth.token_store import TokenStore

logger = logging.getLogger("agente.spotify_explorer_routes")

router = APIRouter()
_token_store = None


def _get_token_store():
    global _token_store
    if _token_store is None:
        _token_store = TokenStore()
    return _token_store


def _resolve_token(session_id):
    try:
        return get_valid_access_token(session_id, _get_token_store())
    except SpotifyNotAuthenticatedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "codigo": "spotify_nao_autenticado",
                "mensagem": "Faça login com o Spotify antes de usar essa função.",
            },
        )


def _call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except SpotifyExplorerError as exc:
        logger.warning("falha ao chamar a Spotify Web API: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "codigo": "spotify_explorer_falhou",
                "mensagem": "Não foi possível completar essa ação no Spotify agora. Tente novamente em instantes.",
            },
        )


# --- 13.1 — Busca ---


@router.get("/explorer/search")
def explorer_search(
    session_id: str = Query(...),
    q: str = Query(...),
    type: str = Query("track"),
    limit: int = Query(10, ge=1, le=50),
):
    token = _resolve_token(session_id)
    return _call(explorer.search, token, q, type, limit)


# --- 13.2 — Detalhes de faixa ---


@router.get("/explorer/track/{track_id}")
def explorer_track(track_id: str, session_id: str = Query(...)):
    token = _resolve_token(session_id)
    return _call(explorer.get_track, token, track_id)


@router.get("/explorer/track/{track_id}/audio-features")
def explorer_audio_features(track_id: str, session_id: str = Query(...)):
    token = _resolve_token(session_id)
    return _call(explorer.get_audio_features, token, track_id)


@router.get("/explorer/track/{track_id}/audio-analysis")
def explorer_audio_analysis(track_id: str, session_id: str = Query(...)):
    token = _resolve_token(session_id)
    return _call(explorer.get_audio_analysis, token, track_id)


# --- 13.3 — Detalhes de artista ---


@router.get("/explorer/artist/{artist_id}")
def explorer_artist(artist_id: str, session_id: str = Query(...)):
    token = _resolve_token(session_id)
    return _call(explorer.get_artist, token, artist_id)


@router.get("/explorer/artist/{artist_id}/top-tracks")
def explorer_artist_top_tracks(artist_id: str, session_id: str = Query(...), market: str = Query("US")):
    token = _resolve_token(session_id)
    return _call(explorer.get_artist_top_tracks, token, artist_id, market)


@router.get("/explorer/artist/{artist_id}/albums")
def explorer_artist_albums(artist_id: str, session_id: str = Query(...)):
    token = _resolve_token(session_id)
    return _call(explorer.get_artist_albums, token, artist_id)


@router.get("/explorer/artist/{artist_id}/related-artists")
def explorer_related_artists(artist_id: str, session_id: str = Query(...)):
    token = _resolve_token(session_id)
    return _call(explorer.get_related_artists, token, artist_id)


# --- 13.4 — Detalhes de álbum ---


@router.get("/explorer/album/{album_id}")
def explorer_album(album_id: str, session_id: str = Query(...)):
    token = _resolve_token(session_id)
    return _call(explorer.get_album, token, album_id)


# --- 13.5 — Detalhes de playlist ---


@router.get("/explorer/playlist/{playlist_id}")
def explorer_playlist(playlist_id: str, session_id: str = Query(...)):
    token = _resolve_token(session_id)
    return _call(explorer.get_playlist, token, playlist_id)


# --- 13.6 — Minhas playlists ---


@router.get("/explorer/me/playlists")
def explorer_my_playlists(session_id: str = Query(...), limit: int = Query(20, ge=1, le=50), offset: int = Query(0, ge=0)):
    token = _resolve_token(session_id)
    return _call(explorer.get_my_playlists, token, limit, offset)


# --- 13.7 — Lançamentos recentes ---


@router.get("/explorer/new-releases")
def explorer_new_releases(session_id: str = Query(...), limit: int = Query(20, ge=1, le=50)):
    token = _resolve_token(session_id)
    return _call(explorer.get_new_releases, token, limit)


# --- 13.8 — Recomendações via API nativa do Spotify ---


@router.get("/explorer/recommendations")
def explorer_recommendations(
    session_id: str = Query(...),
    seed_tracks: str | None = Query(None),
    seed_artists: str | None = Query(None),
    seed_genres: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    token = _resolve_token(session_id)
    params = {"limit": limit}
    if seed_tracks:
        params["seed_tracks"] = seed_tracks
    if seed_artists:
        params["seed_artists"] = seed_artists
    if seed_genres:
        params["seed_genres"] = seed_genres
    if not (seed_tracks or seed_artists or seed_genres):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "codigo": "seed_ausente",
                "mensagem": "Informe pelo menos um seed_tracks, seed_artists ou seed_genres.",
            },
        )
    return _call(explorer.get_recommendations, token, params)


# --- 13.9 — Seguindo ---


@router.get("/explorer/me/following")
def explorer_my_following(session_id: str = Query(...), limit: int = Query(20, ge=1, le=50)):
    token = _resolve_token(session_id)
    return _call(explorer.get_my_following, token, limit)


# --- 13.10 — Meus dados ---


@router.get("/explorer/me")
def explorer_me(session_id: str = Query(...)):
    token = _resolve_token(session_id)
    return _call(explorer.get_me, token)


@router.get("/explorer/me/top/tracks")
def explorer_my_top_tracks(
    session_id: str = Query(...),
    time_range: str = Query("medium_term"),
    limit: int = Query(20, ge=1, le=50),
):
    token = _resolve_token(session_id)
    return _call(explorer.get_my_top_tracks, token, time_range, limit)


@router.get("/explorer/me/top/artists")
def explorer_my_top_artists(
    session_id: str = Query(...),
    time_range: str = Query("medium_term"),
    limit: int = Query(20, ge=1, le=50),
):
    token = _resolve_token(session_id)
    return _call(explorer.get_my_top_artists, token, time_range, limit)


@router.get("/explorer/me/tracks")
def explorer_my_saved_tracks(
    session_id: str = Query(...), limit: int = Query(20, ge=1, le=50), offset: int = Query(0, ge=0)
):
    token = _resolve_token(session_id)
    return _call(explorer.get_my_saved_tracks, token, limit, offset)


@router.get("/explorer/me/player/recently-played")
def explorer_recently_played(session_id: str = Query(...), limit: int = Query(20, ge=1, le=50)):
    token = _resolve_token(session_id)
    return _call(explorer.get_recently_played, token, limit)


# --- 13.11 — Controles de reprodução ---


@router.get("/explorer/me/player")
def explorer_player_state(session_id: str = Query(...)):
    token = _resolve_token(session_id)
    return _call(explorer.get_player_state, token)


@router.get("/explorer/me/player/queue")
def explorer_player_queue(session_id: str = Query(...)):
    token = _resolve_token(session_id)
    return _call(explorer.get_player_queue, token)


@router.post("/explorer/me/player/play")
def explorer_player_play(session_id: str = Query(...)):
    token = _resolve_token(session_id)
    return _call(explorer.player_play, token)


@router.post("/explorer/me/player/pause")
def explorer_player_pause(session_id: str = Query(...)):
    token = _resolve_token(session_id)
    return _call(explorer.player_pause, token)


@router.post("/explorer/me/player/next")
def explorer_player_next(session_id: str = Query(...)):
    token = _resolve_token(session_id)
    return _call(explorer.player_next, token)


@router.post("/explorer/me/player/previous")
def explorer_player_previous(session_id: str = Query(...)):
    token = _resolve_token(session_id)
    return _call(explorer.player_previous, token)


@router.post("/explorer/me/player/seek")
def explorer_player_seek(session_id: str = Query(...), position_ms: int = Query(..., ge=0)):
    token = _resolve_token(session_id)
    return _call(explorer.player_seek, token, position_ms)


@router.post("/explorer/me/player/volume")
def explorer_player_volume(session_id: str = Query(...), volume_percent: int = Query(..., ge=0, le=100)):
    token = _resolve_token(session_id)
    return _call(explorer.player_set_volume, token, volume_percent)


@router.post("/explorer/me/player/shuffle")
def explorer_player_shuffle(session_id: str = Query(...), state: bool = Query(...)):
    token = _resolve_token(session_id)
    return _call(explorer.player_set_shuffle, token, str(state).lower())


@router.post("/explorer/me/player/repeat")
def explorer_player_repeat(session_id: str = Query(...), state: str = Query(..., pattern="^(track|context|off)$")):
    token = _resolve_token(session_id)
    return _call(explorer.player_set_repeat, token, state)
