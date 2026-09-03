import requests

from spotify_auth.history import fetch_recently_played, fetch_saved_tracks, fetch_top_tracks


class _FakeResponse:
    def __init__(self, status_code, body, headers=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._body = body

    def json(self):
        return self._body


def test_fetch_top_tracks_returns_items_on_success(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **kw: _FakeResponse(200, {"items": [{"track_id": "t1"}]}))

    assert fetch_top_tracks("at") == [{"track_id": "t1"}]


def test_fetch_top_tracks_returns_empty_list_on_network_error(monkeypatch):
    def fake_get(*a, **kw):
        raise requests.exceptions.Timeout("demorou demais")

    monkeypatch.setattr(requests, "get", fake_get)

    assert fetch_top_tracks("at") == []


def test_fetch_recently_played_returns_empty_list_on_rate_limit(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **kw: _FakeResponse(429, {}, headers={"Retry-After": "5"}))

    assert fetch_recently_played("at") == []


def test_fetch_recently_played_returns_empty_list_on_error_status(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **kw: _FakeResponse(500, {}))

    assert fetch_recently_played("at") == []


def test_fetch_saved_tracks_follows_pagination_until_next_is_null(monkeypatch):
    pages = [
        {"items": [{"track_id": "t1"}], "next": "https://api.spotify.com/v1/me/tracks?offset=50"},
        {"items": [{"track_id": "t2"}], "next": None},
    ]
    calls = {"n": 0}

    def fake_get(url, headers=None, timeout=None):
        response = _FakeResponse(200, pages[calls["n"]])
        calls["n"] += 1
        return response

    monkeypatch.setattr(requests, "get", fake_get)

    faixas = fetch_saved_tracks("at")

    assert faixas == [{"track_id": "t1"}, {"track_id": "t2"}]
    assert calls["n"] == 2


def test_fetch_saved_tracks_stops_on_partial_failure_mid_pagination(monkeypatch):
    def fake_get(url, headers=None, timeout=None):
        if "offset" in url:
            return _FakeResponse(429, {})
        return _FakeResponse(200, {"items": [{"track_id": "t1"}], "next": "https://api.spotify.com/v1/me/tracks?offset=50"})

    monkeypatch.setattr(requests, "get", fake_get)

    assert fetch_saved_tracks("at") == [{"track_id": "t1"}]
