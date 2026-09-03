from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import spotify_auth.routes as routes
from spotify_auth.client import PendingAuth
from spotify_auth.errors import SpotifyTokenExchangeError


class _FakeTokenStore:
    def __init__(self):
        self.saved = None
        self.deleted = None

    def save(self, session_id, access_token, refresh_token, expires_at):
        self.saved = (session_id, access_token, refresh_token, expires_at)

    def delete(self, session_id):
        self.deleted = session_id


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "client-123")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "secret-456")
    monkeypatch.setattr(routes, "_pending_auth", PendingAuth())
    fake_store = _FakeTokenStore()
    monkeypatch.setattr(routes, "_get_token_store", lambda: fake_store)

    app = FastAPI()
    app.include_router(routes.router)
    with TestClient(app) as test_client:
        test_client.fake_store = fake_store
        yield test_client


def _extract_state(start_response):
    location = start_response.headers["location"]
    return parse_qs(urlparse(location).query)["state"][0]


def test_login_shows_consent_notice_instead_of_redirecting(client):
    response = client.get("/auth/login?session_id=sess-1", follow_redirects=False)

    assert response.status_code == 200
    assert "user-top-read" in response.text
    assert "/auth/login/start?session_id=sess-1" in response.text


def test_login_start_redirects_to_spotify_authorize_url(client):
    response = client.get("/auth/login/start?session_id=sess-1", follow_redirects=False)

    assert response.status_code in (302, 307)
    assert urlparse(response.headers["location"]).netloc == "accounts.spotify.com"


def test_callback_with_error_redirects_without_touching_token_store(client):
    response = client.get("/auth/callback?error=access_denied", follow_redirects=False)

    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/?spotify_login=cancelled"
    assert client.fake_store.saved is None


def test_callback_with_unknown_state_redirects_as_mismatch(client):
    response = client.get("/auth/callback?code=abc&state=nunca-vi-esse-state", follow_redirects=False)

    assert response.headers["location"] == "/?spotify_login=state_mismatch"


def test_callback_happy_path_saves_tokens_and_redirects_success(client, monkeypatch):
    login_response = client.get("/auth/login/start?session_id=sess-1", follow_redirects=False)
    state = _extract_state(login_response)

    monkeypatch.setattr(
        routes,
        "exchange_code_for_tokens",
        lambda code, code_verifier: {"access_token": "at", "refresh_token": "rt", "expires_in": 3600},
    )

    response = client.get(f"/auth/callback?code=auth-code&state={state}", follow_redirects=False)

    assert response.headers["location"] == "/?spotify_login=success"
    session_id, access_token, refresh_token, _ = client.fake_store.saved
    assert (session_id, access_token, refresh_token) == ("sess-1", "at", "rt")


def test_callback_redirects_to_failed_when_token_exchange_fails(client, monkeypatch):
    login_response = client.get("/auth/login/start?session_id=sess-1", follow_redirects=False)
    state = _extract_state(login_response)

    def fake_exchange(code, code_verifier):
        raise SpotifyTokenExchangeError("boom")

    monkeypatch.setattr(routes, "exchange_code_for_tokens", fake_exchange)

    response = client.get(f"/auth/callback?code=auth-code&state={state}", follow_redirects=False)

    assert response.headers["location"] == "/?spotify_login=failed"


def test_logout_deletes_session_tokens(client):
    response = client.post("/auth/logout?session_id=sess-1")

    assert response.status_code == 200
    assert response.json() == {"status": "logged_out"}
    assert client.fake_store.deleted == "sess-1"
