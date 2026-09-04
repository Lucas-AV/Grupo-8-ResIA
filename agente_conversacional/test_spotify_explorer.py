import pytest
import requests

from spotify_auth import explorer
from spotify_auth.errors import SpotifyExplorerError


class _FakeResponse:
    def __init__(self, status_code, body=None, content=b"{}"):
        self.status_code = status_code
        self._body = body
        self.content = content if body is not None else b""

    def json(self):
        return self._body


def test_search_sends_query_type_and_limit(monkeypatch):
    captured = {}

    def fake_request(method, url, headers, params, json, timeout):
        captured.update(method=method, url=url, headers=headers, params=params)
        return _FakeResponse(200, {"tracks": {"items": []}})

    monkeypatch.setattr(requests, "request", fake_request)

    resultado = explorer.search("token-abc", "pagode", "track", 10)

    assert resultado == {"tracks": {"items": []}}
    assert captured["method"] == "GET"
    assert captured["url"] == "https://api.spotify.com/v1/search"
    assert captured["params"] == {"q": "pagode", "type": "track", "limit": 10}
    assert captured["headers"]["Authorization"] == "Bearer token-abc"


def test_get_track_hits_correct_url(monkeypatch):
    monkeypatch.setattr(
        requests, "request", lambda method, url, **kw: _FakeResponse(200, {"id": "t1"})
    )

    assert explorer.get_track("token-abc", "t1") == {"id": "t1"}


def test_raises_spotify_explorer_error_on_4xx_5xx(monkeypatch):
    monkeypatch.setattr(requests, "request", lambda method, url, **kw: _FakeResponse(500, {"error": "boom"}))

    with pytest.raises(SpotifyExplorerError):
        explorer.get_artist("token-abc", "a1")


def test_raises_spotify_explorer_error_on_network_failure(monkeypatch):
    def fake_request(method, url, **kwargs):
        raise requests.exceptions.ConnectionError("recusado")

    monkeypatch.setattr(requests, "request", fake_request)

    with pytest.raises(SpotifyExplorerError):
        explorer.get_album("token-abc", "al1")


def test_returns_empty_dict_on_204_no_content(monkeypatch):
    monkeypatch.setattr(requests, "request", lambda method, url, **kw: _FakeResponse(204, content=b""))

    assert explorer.player_play("token-abc") == {}


def test_player_seek_sends_position_ms_and_uses_put(monkeypatch):
    captured = {}

    def fake_request(method, url, headers, params, json, timeout):
        captured.update(method=method, url=url, params=params)
        return _FakeResponse(204, content=b"")

    monkeypatch.setattr(requests, "request", fake_request)

    explorer.player_seek("token-abc", 5000)

    assert captured["method"] == "PUT"
    assert captured["url"] == "https://api.spotify.com/v1/me/player/seek"
    assert captured["params"] == {"position_ms": 5000}


def test_player_next_uses_post(monkeypatch):
    captured = {}

    def fake_request(method, url, headers, params, json, timeout):
        captured.update(method=method)
        return _FakeResponse(204, content=b"")

    monkeypatch.setattr(requests, "request", fake_request)

    explorer.player_next("token-abc")

    assert captured["method"] == "POST"


def test_get_recommendations_forwards_params_as_is(monkeypatch):
    captured = {}

    def fake_request(method, url, headers, params, json, timeout):
        captured.update(url=url, params=params)
        return _FakeResponse(200, {"tracks": []})

    monkeypatch.setattr(requests, "request", fake_request)

    explorer.get_recommendations("token-abc", {"seed_tracks": "t1,t2", "limit": 5})

    assert captured["url"] == "https://api.spotify.com/v1/recommendations"
    assert captured["params"] == {"seed_tracks": "t1,t2", "limit": 5}


def test_play_track_sends_uris_as_json_body(monkeypatch):
    captured = {}

    def fake_request(method, url, headers, params, json, timeout):
        captured.update(method=method, url=url, params=params, json=json)
        return _FakeResponse(204, content=b"")

    monkeypatch.setattr(requests, "request", fake_request)

    explorer.play_track("token-abc", "spotify:track:t1")

    assert captured["method"] == "PUT"
    assert captured["url"] == "https://api.spotify.com/v1/me/player/play"
    assert captured["json"] == {"uris": ["spotify:track:t1"]}
    assert captured["params"] is None


def test_play_track_forwards_device_id_as_query_param(monkeypatch):
    captured = {}

    def fake_request(method, url, headers, params, json, timeout):
        captured.update(params=params)
        return _FakeResponse(204, content=b"")

    monkeypatch.setattr(requests, "request", fake_request)

    explorer.play_track("token-abc", "spotify:track:t1", device_id="dev-1")

    assert captured["params"] == {"device_id": "dev-1"}


def test_play_track_error_preserves_status_code(monkeypatch):
    monkeypatch.setattr(requests, "request", lambda method, url, **kw: _FakeResponse(404, {"error": "no device"}))

    with pytest.raises(SpotifyExplorerError) as excinfo:
        explorer.play_track("token-abc", "spotify:track:t1")

    assert excinfo.value.status_code == 404


def test_save_track_sends_ids_as_query_param_and_uses_put(monkeypatch):
    captured = {}

    def fake_request(method, url, headers, params, json, timeout):
        captured.update(method=method, url=url, params=params)
        return _FakeResponse(200, content=b"")

    monkeypatch.setattr(requests, "request", fake_request)

    explorer.save_track("token-abc", "t1")

    assert captured["method"] == "PUT"
    assert captured["url"] == "https://api.spotify.com/v1/me/tracks"
    assert captured["params"] == {"ids": "t1"}


def test_save_track_error_preserves_status_code(monkeypatch):
    monkeypatch.setattr(requests, "request", lambda method, url, **kw: _FakeResponse(403, {"error": "forbidden"}))

    with pytest.raises(SpotifyExplorerError) as excinfo:
        explorer.save_track("token-abc", "t1")

    assert excinfo.value.status_code == 403


def test_raises_on_invalid_json_body(monkeypatch):
    class _BadJsonResponse:
        status_code = 200
        content = b"not json"

        def json(self):
            raise ValueError("nao e JSON")

    monkeypatch.setattr(requests, "request", lambda method, url, **kw: _BadJsonResponse())

    with pytest.raises(SpotifyExplorerError):
        explorer.get_me("token-abc")
