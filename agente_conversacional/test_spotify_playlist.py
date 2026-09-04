import pytest
import requests

from spotify_auth.errors import SpotifyPlaylistError
from spotify_auth.playlist import (
    add_tracks,
    create_playlist,
    create_playlist_with_tracks,
    get_current_user_id,
)


class _FakeResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    def json(self):
        return self._body


def test_get_current_user_id_returns_id_from_me(monkeypatch):
    captured = {}

    def fake_get(url, headers, timeout):
        captured["url"] = url
        captured["headers"] = headers
        return _FakeResponse(200, {"id": "usuario-spotify-1"})

    monkeypatch.setattr(requests, "get", fake_get)

    user_id = get_current_user_id("token-abc")

    assert user_id == "usuario-spotify-1"
    assert captured["url"] == "https://api.spotify.com/v1/me"
    assert captured["headers"]["Authorization"] == "Bearer token-abc"


def test_get_current_user_id_raises_on_non_200(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **kw: _FakeResponse(401, {"error": "invalid token"}))

    with pytest.raises(SpotifyPlaylistError):
        get_current_user_id("token-invalido")


def test_get_current_user_id_raises_on_network_error(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.exceptions.ConnectionError("boom")

    monkeypatch.setattr(requests, "get", fake_get)

    with pytest.raises(SpotifyPlaylistError):
        get_current_user_id("token-abc")


def test_create_playlist_posts_name_and_description(monkeypatch):
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured["url"] = url
        captured["json"] = json
        return _FakeResponse(
            201,
            {"id": "playlist-1", "external_urls": {"spotify": "https://open.spotify.com/playlist/playlist-1"}},
        )

    monkeypatch.setattr(requests, "post", fake_post)

    resultado = create_playlist("token-abc", "usuario-1", "Minha playlist", "descricao")

    assert captured["url"] == "https://api.spotify.com/v1/users/usuario-1/playlists"
    assert captured["json"] == {"name": "Minha playlist", "description": "descricao", "public": False}
    assert resultado == {"playlist_id": "playlist-1", "url": "https://open.spotify.com/playlist/playlist-1"}


def test_create_playlist_raises_on_non_2xx(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **kw: _FakeResponse(403, {"error": "forbidden"}))

    with pytest.raises(SpotifyPlaylistError):
        create_playlist("token-abc", "usuario-1", "nome")


def test_add_tracks_sends_uris_and_returns_count(monkeypatch):
    captured = []

    def fake_post(url, headers, json, timeout):
        captured.append((url, json))
        return _FakeResponse(201, {"snapshot_id": "abc"})

    monkeypatch.setattr(requests, "post", fake_post)

    total = add_tracks("token-abc", "playlist-1", ["t1", "t2"])

    assert total == 2
    assert captured[0][0] == "https://api.spotify.com/v1/playlists/playlist-1/tracks"
    assert captured[0][1] == {"uris": ["spotify:track:t1", "spotify:track:t2"]}


def test_add_tracks_chunks_in_batches_of_100(monkeypatch):
    chamadas = []

    def fake_post(url, headers, json, timeout):
        chamadas.append(len(json["uris"]))
        return _FakeResponse(200, {})

    monkeypatch.setattr(requests, "post", fake_post)

    track_ids = [f"t{i}" for i in range(150)]
    total = add_tracks("token-abc", "playlist-1", track_ids)

    assert total == 150
    assert chamadas == [100, 50]


def test_add_tracks_raises_on_non_2xx(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **kw: _FakeResponse(500, {}))

    with pytest.raises(SpotifyPlaylistError):
        add_tracks("token-abc", "playlist-1", ["t1"])


def test_create_playlist_with_tracks_orchestrates_the_full_flow(monkeypatch):
    calls = []

    def fake_get(url, headers, timeout):
        calls.append(("get_me", url))
        return _FakeResponse(200, {"id": "usuario-1"})

    def fake_post(url, headers, json, timeout):
        calls.append(("post", url, json))
        if url.endswith("/playlists"):
            return _FakeResponse(
                201, {"id": "playlist-1", "external_urls": {"spotify": "https://open.spotify.com/playlist/playlist-1"}}
            )
        return _FakeResponse(201, {})

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(requests, "post", fake_post)

    resultado = create_playlist_with_tracks("token-abc", ["t1", "t2"], nome="Minhas faixas")

    assert resultado == {
        "playlist_id": "playlist-1",
        "url": "https://open.spotify.com/playlist/playlist-1",
        "faixas_adicionadas": 2,
    }
    assert calls[0] == ("get_me", "https://api.spotify.com/v1/me")
    assert calls[1][1] == "https://api.spotify.com/v1/users/usuario-1/playlists"
    assert calls[2][1] == "https://api.spotify.com/v1/playlists/playlist-1/tracks"


def test_create_playlist_with_tracks_without_faixas_skips_add_tracks_call(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **kw: _FakeResponse(200, {"id": "usuario-1"}))
    monkeypatch.setattr(
        requests,
        "post",
        lambda *a, **kw: _FakeResponse(201, {"id": "playlist-1", "external_urls": {"spotify": "url"}}),
    )

    resultado = create_playlist_with_tracks("token-abc", [])

    assert resultado["faixas_adicionadas"] == 0
