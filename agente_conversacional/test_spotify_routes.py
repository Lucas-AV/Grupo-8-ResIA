from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import spotify_auth.routes as routes
from spotify_auth.client import PendingAuth
from spotify_auth.errors import SpotifyNotAuthenticatedError, SpotifyPlaylistError, SpotifyTokenExchangeError
from spotify_auth.pairing_store import PairingStore


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
    monkeypatch.setattr(routes, "_pairing_store", PairingStore())
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
        lambda code, code_verifier, redirect_uri: {"access_token": "at", "refresh_token": "rt", "expires_in": 3600},
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

    def fake_exchange(code, code_verifier, redirect_uri):
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


# --- 12.6 — Sugestão de título/descrição via LLM (modal de "Salvar no Spotify") ---


def test_sugerir_playlist_devolve_titulo_e_descricao_do_llm(client, monkeypatch):
    captured = {}

    def fake_sugerir(faixas):
        captured["faixas"] = faixas
        return {"titulo": "Pagode pra Domingo", "descricao": "Clássicos animados."}

    monkeypatch.setattr(routes, "sugerir_titulo_descricao", fake_sugerir)

    response = client.post(
        "/playlist/sugerir",
        json={"faixas": [{"track_id": "t1", "nome": "Faixa", "artista": "Artista", "album": "Album", "genero": "pagode"}]},
    )

    assert response.status_code == 200
    assert response.json() == {"titulo": "Pagode pra Domingo", "descricao": "Clássicos animados."}
    assert captured["faixas"] == [{"track_id": "t1", "nome": "Faixa", "artista": "Artista", "album": "Album", "genero": "pagode"}]


def test_sugerir_playlist_rejects_empty_faixas(client):
    response = client.post("/playlist/sugerir", json={"faixas": []})

    assert response.status_code == 422


def test_sugerir_playlist_nao_exige_sessao_autenticada(client, monkeypatch):
    """So gera texto via LLM — nao fala com a Spotify, entao nao precisa
    de token/sessao (diferente de /playlist/criar)."""
    monkeypatch.setattr(routes, "sugerir_titulo_descricao", lambda faixas: {"titulo": "X", "descricao": "Y"})

    response = client.post(
        "/playlist/sugerir",
        json={"faixas": [{"track_id": "t1", "nome": "Faixa", "artista": "Artista", "album": "Album", "genero": "pop"}]},
    )

    assert response.status_code == 200


# --- 13.13 — Login via QR code (pareamento) ---


def test_auth_qr_returns_code_and_svg_data_uri(client):
    response = client.get("/auth/qr?session_id=kiosk-1")

    assert response.status_code == 200
    body = response.json()
    assert body["code"]
    assert body["qr_svg_data_uri"].startswith("data:image/svg+xml")
    assert "pair=" + body["code"] in body["pair_login_url"]
    assert "/auth/login/start" in body["pair_login_url"]


def test_pair_status_not_found_for_unknown_code(client):
    response = client.get("/auth/pair/codigo-que-nao-existe/status?session_id=kiosk-1")

    assert response.status_code == 200
    assert response.json() == {"status": "not_found"}


def test_pair_status_pending_before_phone_completes_oauth(client):
    qr = client.get("/auth/qr?session_id=kiosk-1").json()

    response = client.get(f"/auth/pair/{qr['code']}/status?session_id=kiosk-1")

    assert response.json() == {"status": "pending"}


def test_callback_with_pair_code_relays_tokens_and_does_not_touch_kiosk_session_yet(client, monkeypatch):
    qr = client.get("/auth/qr?session_id=kiosk-1").json()
    login_response = client.get(
        f"/auth/login/start?session_id=qr-pair-phone&pair={qr['code']}", follow_redirects=False
    )
    state = _extract_state(login_response)

    monkeypatch.setattr(
        routes,
        "exchange_code_for_tokens",
        lambda code, code_verifier, redirect_uri: {"access_token": "at-phone", "refresh_token": "rt-phone", "expires_in": 3600},
    )

    response = client.get(f"/auth/callback?code=auth-code&state={state}", follow_redirects=False)

    assert response.status_code == 200
    assert "Spotify conectado" in response.text
    # tokens ainda nao foram salvos em nenhuma sessao — so no relay, ate o kiosk consumir
    assert client.fake_store.saved is None


def _completar_pareamento_no_celular(client, monkeypatch):
    """Percorre o fluxo do celular (QR -> login/start -> callback) e devolve a resposta do callback."""
    qr = client.get("/auth/qr?session_id=kiosk-1").json()
    login_response = client.get(
        f"/auth/login/start?session_id=qr-pair-phone&pair={qr['code']}", follow_redirects=False
    )
    state = _extract_state(login_response)
    monkeypatch.setattr(
        routes,
        "exchange_code_for_tokens",
        lambda code, code_verifier, redirect_uri: {"access_token": "at-phone", "refresh_token": "rt-phone", "expires_in": 3600},
    )
    return client.get(f"/auth/callback?code=auth-code&state={state}", follow_redirects=False)


def test_pairing_success_page_offers_spotify_deep_link_and_web_fallback(client, monkeypatch):
    """A página que o celular recebe abre o app do Spotify: deep link (esquema
    `spotify:`) na tentativa automática/no botão e link universal
    `https://open.spotify.com/` como fallback quando o app não está instalado."""
    response = _completar_pareamento_no_celular(client, monkeypatch)

    assert response.status_code == 200
    pagina = response.text
    assert routes._SPOTIFY_APP_URI in pagina
    assert routes._SPOTIFY_APP_URI.startswith("spotify://")
    assert routes._SPOTIFY_WEB_URL in pagina
    assert f'href="{routes._SPOTIFY_WEB_URL}"' in pagina  # fallback funciona mesmo sem JS
    assert 'id="abrir-spotify"' in pagina
    assert "Abrir o Spotify" in pagina


def test_pairing_success_page_keeps_reassurance_copy(client, monkeypatch):
    """Abrir o Spotify não pode dar a impressão de que o pareamento falhou ou
    de que a pessoa precisa continuar no celular."""
    pagina = _completar_pareamento_no_celular(client, monkeypatch).text

    assert "Spotify conectado" in pagina
    assert "voltar pro outro dispositivo" in pagina.lower()
    assert "fechar essa aba" in pagina.lower()


def test_pairing_success_page_is_self_contained(client, monkeypatch):
    """Página servida solta pelo backend no celular: CSS/JS inline, nenhuma
    dependência de CDN ou do frontend/style.css (a demo roda em rede local)."""
    pagina = _completar_pareamento_no_celular(client, monkeypatch).text

    assert "<style>" in pagina and "<script>" in pagina
    assert "stylesheet" not in pagina
    assert "fonts.googleapis.com" not in pagina
    assert "cdn" not in pagina.lower()


def test_pair_status_completed_saves_tokens_into_kiosk_session(client, monkeypatch):
    qr = client.get("/auth/qr?session_id=kiosk-1").json()
    login_response = client.get(
        f"/auth/login/start?session_id=qr-pair-phone&pair={qr['code']}", follow_redirects=False
    )
    state = _extract_state(login_response)
    monkeypatch.setattr(
        routes,
        "exchange_code_for_tokens",
        lambda code, code_verifier, redirect_uri: {"access_token": "at-phone", "refresh_token": "rt-phone", "expires_in": 3600},
    )
    client.get(f"/auth/callback?code=auth-code&state={state}", follow_redirects=False)

    response = client.get(f"/auth/pair/{qr['code']}/status?session_id=kiosk-1")

    assert response.json() == {"status": "completed"}
    session_id, access_token, refresh_token, _ = client.fake_store.saved
    assert (session_id, access_token, refresh_token) == ("kiosk-1", "at-phone", "rt-phone")
    assert client.fake_session_store.authenticated_sessions == ["kiosk-1"]


def test_pair_status_is_one_shot_second_poll_after_completed_returns_not_found(client, monkeypatch):
    qr = client.get("/auth/qr?session_id=kiosk-1").json()
    login_response = client.get(
        f"/auth/login/start?session_id=qr-pair-phone&pair={qr['code']}", follow_redirects=False
    )
    state = _extract_state(login_response)
    monkeypatch.setattr(
        routes,
        "exchange_code_for_tokens",
        lambda code, code_verifier, redirect_uri: {"access_token": "at", "refresh_token": "rt", "expires_in": 3600},
    )
    client.get(f"/auth/callback?code=auth-code&state={state}", follow_redirects=False)
    client.get(f"/auth/pair/{qr['code']}/status?session_id=kiosk-1")

    response = client.get(f"/auth/pair/{qr['code']}/status?session_id=kiosk-1")

    assert response.json() == {"status": "not_found"}


def test_callback_with_expired_pair_code_returns_410(client, monkeypatch):
    login_response = client.get(
        "/auth/login/start?session_id=qr-pair-phone&pair=codigo-que-ja-expirou", follow_redirects=False
    )
    state = _extract_state(login_response)
    monkeypatch.setattr(
        routes,
        "exchange_code_for_tokens",
        lambda code, code_verifier, redirect_uri: {"access_token": "at", "refresh_token": "rt", "expires_in": 3600},
    )

    response = client.get(f"/auth/callback?code=auth-code&state={state}", follow_redirects=False)

    assert response.status_code == 410
    assert "expirou" in response.text.lower()


def test_normal_login_start_without_pair_still_works(client):
    """Garante que o parametro `pair` opcional nao quebrou o fluxo de login normal (4.4/5.x)."""
    response = client.get("/auth/login/start?session_id=sess-1", follow_redirects=False)

    assert response.status_code in (302, 307)
    assert "pair=" not in response.headers["location"]
