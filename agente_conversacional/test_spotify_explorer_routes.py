import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import spotify_auth.explorer_routes as explorer_routes
from spotify_auth.errors import SpotifyExplorerError, SpotifyNotAuthenticatedError


class _FakeTokenStore:
    def __init__(self, tokens_by_session=None):
        self._tokens = dict(tokens_by_session or {})

    def get(self, session_id):
        return self._tokens.get(session_id)

    def save(self, *args, **kwargs):
        raise AssertionError("explorer routes nunca devem salvar tokens")

    def delete(self, *args, **kwargs):
        raise AssertionError("explorer routes nunca devem apagar tokens")


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(explorer_routes, "_token_store", _FakeTokenStore())
    monkeypatch.setattr(explorer_routes, "_get_token_store", lambda: explorer_routes._token_store)
    monkeypatch.setattr(
        explorer_routes, "get_valid_access_token", lambda session_id, token_store, timeout=None: "token-valido"
    )

    app = FastAPI()
    app.include_router(explorer_routes.router)
    with TestClient(app) as test_client:
        yield test_client


def _sem_token(monkeypatch):
    def fake(session_id, token_store, timeout=None):
        raise SpotifyNotAuthenticatedError(session_id)

    monkeypatch.setattr(explorer_routes, "get_valid_access_token", fake)


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/explorer/search?session_id=s&q=pagode"),
        ("get", "/explorer/track/t1?session_id=s"),
        ("get", "/explorer/artist/a1?session_id=s"),
        ("get", "/explorer/album/al1?session_id=s"),
        ("get", "/explorer/playlist/p1?session_id=s"),
        ("get", "/explorer/me?session_id=s"),
        ("get", "/explorer/me/playlists?session_id=s"),
        ("get", "/explorer/new-releases?session_id=s"),
        ("get", "/explorer/me/player?session_id=s"),
        ("post", "/explorer/me/player/play?session_id=s"),
    ],
)
def test_returns_401_when_session_not_authenticated(client, monkeypatch, method, path):
    _sem_token(monkeypatch)

    response = getattr(client, method)(path)

    assert response.status_code == 401
    assert response.json()["detail"]["codigo"] == "spotify_nao_autenticado"


def test_search_calls_explorer_with_query_params(client, monkeypatch):
    captured = {}

    def fake_search(access_token, query, tipo, limit):
        captured.update(access_token=access_token, query=query, tipo=tipo, limit=limit)
        return {"tracks": {"items": []}}

    monkeypatch.setattr(explorer_routes.explorer, "search", fake_search)

    response = client.get("/explorer/search?session_id=s&q=pagode&type=track&limit=5")

    assert response.status_code == 200
    assert response.json() == {"tracks": {"items": []}}
    assert captured == {"access_token": "token-valido", "query": "pagode", "tipo": "track", "limit": 5}


def test_track_endpoints_delegate_to_explorer(client, monkeypatch):
    monkeypatch.setattr(explorer_routes.explorer, "get_track", lambda token, tid: {"id": tid})
    monkeypatch.setattr(explorer_routes.explorer, "get_audio_features", lambda token, tid: {"danceability": 0.8})
    monkeypatch.setattr(explorer_routes.explorer, "get_audio_analysis", lambda token, tid: {"track": {}})

    assert client.get("/explorer/track/t1?session_id=s").json() == {"id": "t1"}
    assert client.get("/explorer/track/t1/audio-features?session_id=s").json() == {"danceability": 0.8}
    assert client.get("/explorer/track/t1/audio-analysis?session_id=s").json() == {"track": {}}


def test_artist_endpoints_delegate_to_explorer(client, monkeypatch):
    monkeypatch.setattr(explorer_routes.explorer, "get_artist", lambda token, aid: {"id": aid})
    monkeypatch.setattr(
        explorer_routes.explorer, "get_artist_top_tracks", lambda token, aid, market: {"tracks": [], "market": market}
    )
    monkeypatch.setattr(explorer_routes.explorer, "get_artist_albums", lambda token, aid: {"items": []})
    monkeypatch.setattr(explorer_routes.explorer, "get_related_artists", lambda token, aid: {"artists": []})

    assert client.get("/explorer/artist/a1?session_id=s").json() == {"id": "a1"}
    resposta = client.get("/explorer/artist/a1/top-tracks?session_id=s&market=BR").json()
    assert resposta == {"tracks": [], "market": "BR"}
    assert client.get("/explorer/artist/a1/albums?session_id=s").json() == {"items": []}
    assert client.get("/explorer/artist/a1/related-artists?session_id=s").json() == {"artists": []}


def test_album_and_playlist_endpoints_delegate_to_explorer(client, monkeypatch):
    monkeypatch.setattr(explorer_routes.explorer, "get_album", lambda token, alid: {"id": alid})
    monkeypatch.setattr(explorer_routes.explorer, "get_playlist", lambda token, pid: {"id": pid})

    assert client.get("/explorer/album/al1?session_id=s").json() == {"id": "al1"}
    assert client.get("/explorer/playlist/p1?session_id=s").json() == {"id": "p1"}


def test_new_releases_and_my_playlists_delegate_to_explorer(client, monkeypatch):
    monkeypatch.setattr(explorer_routes.explorer, "get_new_releases", lambda token, limit: {"albums": {"items": []}})
    monkeypatch.setattr(
        explorer_routes.explorer, "get_my_playlists", lambda token, limit, offset: {"items": [], "offset": offset}
    )

    assert client.get("/explorer/new-releases?session_id=s").json() == {"albums": {"items": []}}
    assert client.get("/explorer/me/playlists?session_id=s&offset=10").json() == {"items": [], "offset": 10}


def test_recommendations_requires_at_least_one_seed(client):
    response = client.get("/explorer/recommendations?session_id=s")

    assert response.status_code == 400
    assert response.json()["detail"]["codigo"] == "seed_ausente"


def test_recommendations_forwards_seeds_to_explorer(client, monkeypatch):
    captured = {}

    def fake_recommendations(token, params):
        captured.update(params)
        return {"tracks": []}

    monkeypatch.setattr(explorer_routes.explorer, "get_recommendations", fake_recommendations)

    response = client.get("/explorer/recommendations?session_id=s&seed_tracks=t1,t2&limit=5")

    assert response.status_code == 200
    assert captured == {"seed_tracks": "t1,t2", "limit": 5}


def test_me_and_user_data_endpoints_delegate_to_explorer(client, monkeypatch):
    monkeypatch.setattr(explorer_routes.explorer, "get_me", lambda token: {"id": "user-1"})
    monkeypatch.setattr(
        explorer_routes.explorer, "get_my_top_tracks", lambda token, time_range, limit: {"time_range": time_range}
    )
    monkeypatch.setattr(
        explorer_routes.explorer, "get_my_top_artists", lambda token, time_range, limit: {"time_range": time_range}
    )
    monkeypatch.setattr(
        explorer_routes.explorer, "get_my_saved_tracks", lambda token, limit, offset: {"offset": offset}
    )
    monkeypatch.setattr(explorer_routes.explorer, "get_recently_played", lambda token, limit: {"items": []})
    monkeypatch.setattr(explorer_routes.explorer, "get_my_following", lambda token, limit: {"artists": {}})

    assert client.get("/explorer/me?session_id=s").json() == {"id": "user-1"}
    assert client.get("/explorer/me/top/tracks?session_id=s&time_range=short_term").json() == {
        "time_range": "short_term"
    }
    assert client.get("/explorer/me/top/artists?session_id=s").json() == {"time_range": "medium_term"}
    assert client.get("/explorer/me/tracks?session_id=s&offset=5").json() == {"offset": 5}
    assert client.get("/explorer/me/player/recently-played?session_id=s").json() == {"items": []}
    assert client.get("/explorer/me/following?session_id=s").json() == {"artists": {}}


def test_player_state_and_queue_delegate_to_explorer(client, monkeypatch):
    monkeypatch.setattr(explorer_routes.explorer, "get_player_state", lambda token: {"is_playing": True})
    monkeypatch.setattr(explorer_routes.explorer, "get_player_queue", lambda token: {"queue": []})

    assert client.get("/explorer/me/player?session_id=s").json() == {"is_playing": True}
    assert client.get("/explorer/me/player/queue?session_id=s").json() == {"queue": []}


def test_player_control_actions_delegate_to_explorer(client, monkeypatch):
    calls = []
    monkeypatch.setattr(explorer_routes.explorer, "player_play", lambda token: calls.append("play") or {})
    monkeypatch.setattr(explorer_routes.explorer, "player_pause", lambda token: calls.append("pause") or {})
    monkeypatch.setattr(explorer_routes.explorer, "player_next", lambda token: calls.append("next") or {})
    monkeypatch.setattr(explorer_routes.explorer, "player_previous", lambda token: calls.append("previous") or {})
    monkeypatch.setattr(
        explorer_routes.explorer,
        "player_seek",
        lambda token, position_ms: calls.append(("seek", position_ms)) or {},
    )
    monkeypatch.setattr(
        explorer_routes.explorer,
        "player_set_volume",
        lambda token, volume_percent: calls.append(("volume", volume_percent)) or {},
    )
    monkeypatch.setattr(
        explorer_routes.explorer, "player_set_shuffle", lambda token, state: calls.append(("shuffle", state)) or {}
    )
    monkeypatch.setattr(
        explorer_routes.explorer, "player_set_repeat", lambda token, state: calls.append(("repeat", state)) or {}
    )

    assert client.post("/explorer/me/player/play?session_id=s").status_code == 200
    assert client.post("/explorer/me/player/pause?session_id=s").status_code == 200
    assert client.post("/explorer/me/player/next?session_id=s").status_code == 200
    assert client.post("/explorer/me/player/previous?session_id=s").status_code == 200
    assert client.post("/explorer/me/player/seek?session_id=s&position_ms=1000").status_code == 200
    assert client.post("/explorer/me/player/volume?session_id=s&volume_percent=80").status_code == 200
    assert client.post("/explorer/me/player/shuffle?session_id=s&state=true").status_code == 200
    assert client.post("/explorer/me/player/repeat?session_id=s&state=track").status_code == 200

    assert calls == [
        "play",
        "pause",
        "next",
        "previous",
        ("seek", 1000),
        ("volume", 80),
        ("shuffle", "true"),
        ("repeat", "track"),
    ]


def test_repeat_rejects_invalid_state(client):
    response = client.post("/explorer/me/player/repeat?session_id=s&state=bogus")

    assert response.status_code == 422


def test_spotify_explorer_error_becomes_502(client, monkeypatch):
    def fake_search(access_token, query, tipo, limit):
        raise SpotifyExplorerError("Spotify respondeu HTTP 500 em GET /search")

    monkeypatch.setattr(explorer_routes.explorer, "search", fake_search)

    response = client.get("/explorer/search?session_id=s&q=pagode")

    assert response.status_code == 502
    assert response.json()["detail"]["codigo"] == "spotify_explorer_falhou"
