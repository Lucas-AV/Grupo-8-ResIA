import time
from urllib.parse import parse_qs, urlparse

import pytest
import requests

from spotify_auth.client import (
    PendingAuth,
    build_authorize_url,
    exchange_code_for_tokens,
    get_valid_access_token,
    refresh_access_token,
)
from spotify_auth.errors import SpotifyNotAuthenticatedError, SpotifyTokenExchangeError


class _FakeResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    def json(self):
        return self._body


class _FakeTokenStore:
    def __init__(self, tokens_by_session=None):
        self._tokens = dict(tokens_by_session or {})
        self.saved = []
        self.deleted = []

    def get(self, session_id):
        return self._tokens.get(session_id)

    def save(self, session_id, access_token, refresh_token, expires_at):
        self._tokens[session_id] = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
        }
        self.saved.append(session_id)

    def delete(self, session_id):
        self._tokens.pop(session_id, None)
        self.deleted.append(session_id)


@pytest.fixture(autouse=True)
def spotify_env(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "client-123")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "secret-456")
    monkeypatch.setenv("SPOTIFY_REDIRECT_URI", "http://localhost:8000/auth/callback")


def test_build_authorize_url_includes_pkce_challenge_and_registers_pending_state():
    pending_auth = PendingAuth()

    url = build_authorize_url("sess-1", pending_auth)

    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    assert parsed.netloc == "accounts.spotify.com"
    assert params["client_id"] == ["client-123"]
    assert params["code_challenge_method"] == ["S256"]
    assert "code_challenge" in params

    state = params["state"][0]
    pending = pending_auth.consume(state)
    assert pending["session_id"] == "sess-1"
    assert "code_verifier" in pending


def test_exchange_code_for_tokens_posts_authorization_code_grant(monkeypatch):
    captured = {}

    def fake_post(url, data, auth, timeout):
        captured["url"] = url
        captured["data"] = data
        captured["auth"] = auth
        return _FakeResponse(200, {"access_token": "at", "refresh_token": "rt", "expires_in": 3600})

    monkeypatch.setattr(requests, "post", fake_post)

    tokens = exchange_code_for_tokens("auth-code", "verifier-abc")

    assert tokens == {"access_token": "at", "refresh_token": "rt", "expires_in": 3600}
    assert captured["data"]["grant_type"] == "authorization_code"
    assert captured["data"]["code_verifier"] == "verifier-abc"
    assert captured["auth"] == ("client-123", "secret-456")


def test_exchange_code_for_tokens_raises_on_non_200(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **kw: _FakeResponse(400, {"error": "invalid_grant"}))

    with pytest.raises(SpotifyTokenExchangeError):
        exchange_code_for_tokens("bad-code", "verifier-abc")


def test_exchange_code_for_tokens_raises_on_network_error(monkeypatch):
    def fake_post(*args, **kwargs):
        raise requests.exceptions.ConnectionError("boom")

    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(SpotifyTokenExchangeError):
        exchange_code_for_tokens("code", "verifier")


def test_refresh_access_token_keeps_old_refresh_token_when_not_returned(monkeypatch):
    monkeypatch.setattr(
        requests, "post", lambda *a, **kw: _FakeResponse(200, {"access_token": "new-at", "expires_in": 3600})
    )

    tokens = refresh_access_token("old-rt")

    assert tokens == {"access_token": "new-at", "refresh_token": "old-rt", "expires_in": 3600}


def test_get_valid_access_token_returns_cached_token_without_refreshing(monkeypatch):
    store = _FakeTokenStore({"sess-1": {"access_token": "at", "refresh_token": "rt", "expires_at": time.time() + 3600}})
    monkeypatch.setattr(requests, "post", lambda *a, **kw: pytest.fail("nao deveria chamar o Spotify"))

    assert get_valid_access_token("sess-1", store) == "at"


def test_get_valid_access_token_refreshes_when_close_to_expiry(monkeypatch):
    store = _FakeTokenStore({"sess-1": {"access_token": "old-at", "refresh_token": "rt", "expires_at": time.time() + 10}})
    monkeypatch.setattr(
        requests,
        "post",
        lambda *a, **kw: _FakeResponse(200, {"access_token": "new-at", "refresh_token": "new-rt", "expires_in": 3600}),
    )

    token = get_valid_access_token("sess-1", store)

    assert token == "new-at"
    assert store.saved == ["sess-1"]


def test_get_valid_access_token_raises_when_session_never_logged_in():
    store = _FakeTokenStore()

    with pytest.raises(SpotifyNotAuthenticatedError):
        get_valid_access_token("sess-nunca-logou", store)


def test_get_valid_access_token_falls_back_to_anonymous_when_refresh_token_revoked(monkeypatch):
    store = _FakeTokenStore({"sess-1": {"access_token": "old-at", "refresh_token": "revoked-rt", "expires_at": time.time() + 10}})
    monkeypatch.setattr(requests, "post", lambda *a, **kw: _FakeResponse(400, {"error": "invalid_grant"}))

    with pytest.raises(SpotifyNotAuthenticatedError):
        get_valid_access_token("sess-1", store)

    assert store.deleted == ["sess-1"]
