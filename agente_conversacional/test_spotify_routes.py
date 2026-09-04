from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import spotify_auth.routes as routes
from spotify_auth.client import PendingAuth
from spotify_auth.errors import SpotifyNotAuthenticatedError, SpotifyPlaylistError, SpotifyTokenExchangeError


class _FakeTokenStore:
    def __init__(self, tokens_by_session=None):
        self._tokens = dict(tokens_by_session or {})
        self.saved = None
        self.deleted = None

    def get(self, session_id):
        return self._tokens.get(session_id)

    def save(self, session_id, access_token, refresh_token, expires_at):
        self._tokens[session_id] = {"access_token": access_token, "refresh_token": refresh_token, "expires_at": expires_at}
        self.saved = (session_id, access_token, refresh_token, expires_at)

    def delete(self, session_id):
        self._tokens.pop(session_id, None)
        self.deleted = session_id


class _FakeSessionStore:
    def __init__(self):
        self.authenticated_sessions = []

    def mark_authenticated(self, session_id, perfil_usuario=None):
        self.authenticated_sessions.append(session_id)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "client-123")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "secret-456")
    monkeypatch.setattr(routes, "_pending_auth", PendingAuth())
    fake_store = _FakeTokenStore()
    monkeypatch.setattr(routes, "_get_token_store", lambda: fake_store)

    app = FastAPI()
    app.state.session_store = _FakeSessionStore()
    app.include_router(routes.router)
    with TestClient(app) as test_client:
        test_client.fake_store = fake_store
        test_client.fake_session_store = app.state.session_store
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
    monkeypatch.setattr(routes, "_perfil_e_cobertura_do_historico", lambda token: (0.1, 0.2))

    response = client.get(f"/auth/callback?code=auth-code&state={state}", follow_redirects=False)

    assert response.headers["location"] == "/?spotify_login=success"
    session_id, access_token, refresh_token, _ = client.fake_store.saved
    assert (session_id, access_token, refresh_token) == ("sess-1", "at", "rt")
    assert client.fake_session_store.authenticated_sessions == ["sess-1"]


def test_login_com_historico_registra_cobertura_sem_expor_token(monkeypatch, caplog):
    monkeypatch.setattr(routes, "fetch_top_tracks", lambda token: [{"id": "t1"}])
    monkeypatch.setattr(routes, "fetch_recently_played", lambda token: [])
    monkeypatch.setattr(routes, "fetch_saved_tracks", lambda token: [])
    monkeypatch.setattr(routes, "casar_historico_com_dataset", lambda historico: {
        "taxa_cobertura": 0.5, "total_casadas": 1, "total_historico": 2,
    })
    monkeypatch.setattr(routes, "calcular_perfil_usuario", lambda historico: None)

    with caplog.at_level("INFO", logger="agente.spotify_auth"):
        assert routes._perfil_e_cobertura_do_historico("token-secreto") is None

    assert "cobertura_matching_oauth=50.0%" in caplog.records[-1].message
    assert "token-secreto" not in caplog.records[-1].message


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


def test_auth_status_true_when_session_has_tokens(client):
    client.fake_store.save("sess-1", "at", "rt", 9999999999)

    response = client.get("/auth/status?session_id=sess-1")

    assert response.status_code == 200
    assert response.json() == {"autenticado": True}


def test_auth_status_false_when_session_never_logged_in(client):
    response = client.get("/auth/status?session_id=sess-nunca-logou")

    assert response.status_code == 200
    assert response.json() == {"autenticado": False}


def test_criar_playlist_returns_401_when_session_not_authenticated(client, monkeypatch):
    def fake_get_valid_access_token(session_id, token_store, timeout=None):
        raise SpotifyNotAuthenticatedError(session_id)

    monkeypatch.setattr(routes, "get_valid_access_token", fake_get_valid_access_token)

    response = client.post("/playlist/criar", json={"session_id": "sess-anonima", "faixas": ["t1"]})

    assert response.status_code == 401
    assert response.json()["detail"]["codigo"] == "spotify_nao_autenticado"


def test_criar_playlist_creates_playlist_with_valid_token(client, monkeypatch):
    monkeypatch.setattr(routes, "get_valid_access_token", lambda session_id, token_store, timeout=None: "at-valido")

    captured = {}

    def fake_create_playlist_with_tracks(access_token, faixas, nome=None, descricao=None, timeout=None):
        captured["access_token"] = access_token
        captured["faixas"] = faixas
        captured["nome"] = nome
        return {"playlist_id": "playlist-1", "url": "https://open.spotify.com/playlist/playlist-1", "faixas_adicionadas": 2}

    monkeypatch.setattr(routes, "create_playlist_with_tracks", fake_create_playlist_with_tracks)

    response = client.post(
        "/playlist/criar",
        json={"session_id": "sess-1", "faixas": ["t1", "t2"], "nome": "Minhas faixas"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "playlist_id": "playlist-1",
        "url": "https://open.spotify.com/playlist/playlist-1",
        "faixas_adicionadas": 2,
    }
    assert captured == {"access_token": "at-valido", "faixas": ["t1", "t2"], "nome": "Minhas faixas"}


def test_criar_playlist_returns_502_when_spotify_call_fails(client, monkeypatch):
    monkeypatch.setattr(routes, "get_valid_access_token", lambda session_id, token_store, timeout=None: "at-valido")

    def fake_create_playlist_with_tracks(*args, **kwargs):
        raise SpotifyPlaylistError("Spotify respondeu HTTP 500 ao criar a playlist")

    monkeypatch.setattr(routes, "create_playlist_with_tracks", fake_create_playlist_with_tracks)

    response = client.post("/playlist/criar", json={"session_id": "sess-1", "faixas": ["t1"]})

    assert response.status_code == 502
    assert response.json()["detail"]["codigo"] == "spotify_playlist_falhou"


def test_criar_playlist_rejects_empty_faixas(client):
    response = client.post("/playlist/criar", json={"session_id": "sess-1", "faixas": []})

    assert response.status_code == 422
