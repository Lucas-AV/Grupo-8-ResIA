import app as app_module


def test_login_redirects_to_spotify_authorize(client):
    response = client.get("/login")

    assert response.status_code == 302
    assert response.location.startswith("https://accounts.spotify.com/authorize")


def test_callback_exchanges_code_and_redirects_home(client, monkeypatch):
    calls = {}

    def fake_exchange_code(code, state, client_id, client_secret, redirect_uri):
        calls["code"] = code
        calls["state"] = state

    monkeypatch.setattr(app_module.user_auth, "exchange_code", fake_exchange_code)

    response = client.get("/callback?code=abc&state=xyz")

    assert response.status_code == 302
    assert response.location.endswith("/")
    assert calls == {"code": "abc", "state": "xyz"}


def test_callback_with_spotify_error_redirects_with_auth_error(client):
    response = client.get("/callback?error=access_denied")

    assert response.status_code == 302
    assert "auth_error=access_denied" in response.location


def test_callback_with_bad_state_redirects_with_auth_error(client, monkeypatch):
    def fake_exchange_code(code, state, client_id, client_secret, redirect_uri):
        raise ValueError("state inválido")

    monkeypatch.setattr(app_module.user_auth, "exchange_code", fake_exchange_code)

    response = client.get("/callback?code=abc&state=bad")

    assert response.status_code == 302
    assert "auth_error=" in response.location


def test_logout_clears_session_and_redirects_home(client, monkeypatch):
    calls = {"logged_out": False}

    def fake_logout():
        calls["logged_out"] = True

    monkeypatch.setattr(app_module.user_auth, "logout", fake_logout)

    response = client.get("/logout")

    assert response.status_code == 302
    assert calls["logged_out"] is True


def test_me_returns_401_when_not_logged_in(client, monkeypatch):
    def fake_get_valid_user_token(client_id, client_secret):
        raise app_module.user_auth.NotLoggedInError("faça login primeiro em /login")

    monkeypatch.setattr(app_module.user_auth, "get_valid_user_token", fake_get_valid_user_token)

    response = client.get("/api/me")

    assert response.status_code == 401
    assert "login" in response.get_json()["error"]


def test_me_returns_profile_when_logged_in(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )

    def fake_call_api(path, token, params=None):
        assert path == "/me"
        assert token == "user-token"
        return {"display_name": "Test User"}, 200

    monkeypatch.setattr(app_module.spotify_client, "call_api", fake_call_api)

    response = client.get("/api/me")

    assert response.status_code == 200
    assert response.get_json() == {"display_name": "Test User"}


def test_top_tracks_requires_login(client, monkeypatch):
    def fake_get_valid_user_token(client_id, client_secret):
        raise app_module.user_auth.NotLoggedInError("faça login primeiro em /login")

    monkeypatch.setattr(app_module.user_auth, "get_valid_user_token", fake_get_valid_user_token)

    response = client.get("/api/me/top/tracks")

    assert response.status_code == 401


def test_top_tracks_uses_time_range_and_limit(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )

    def fake_call_api(path, token, params=None):
        assert path == "/me/top/tracks"
        assert params == {"time_range": "long_term", "limit": "5"}
        return {"items": []}, 200

    monkeypatch.setattr(app_module.spotify_client, "call_api", fake_call_api)

    response = client.get("/api/me/top/tracks?time_range=long_term&limit=5")

    assert response.status_code == 200


def test_top_tracks_defaults_to_medium_term(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )

    def fake_call_api(path, token, params=None):
        assert params["time_range"] == "medium_term"
        return {"items": []}, 200

    monkeypatch.setattr(app_module.spotify_client, "call_api", fake_call_api)

    response = client.get("/api/me/top/tracks")

    assert response.status_code == 200


def test_top_artists_uses_time_range(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )

    def fake_call_api(path, token, params=None):
        assert path == "/me/top/artists"
        assert params["time_range"] == "short_term"
        return {"items": []}, 200

    monkeypatch.setattr(app_module.spotify_client, "call_api", fake_call_api)

    response = client.get("/api/me/top/artists?time_range=short_term")

    assert response.status_code == 200


def test_saved_tracks_calls_correct_path(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )

    def fake_call_api(path, token, params=None):
        assert path == "/me/tracks"
        return {"items": []}, 200

    monkeypatch.setattr(app_module.spotify_client, "call_api", fake_call_api)

    response = client.get("/api/me/tracks")

    assert response.status_code == 200


def test_recently_played_calls_correct_path(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )

    def fake_call_api(path, token, params=None):
        assert path == "/me/player/recently-played"
        return {"items": []}, 200

    monkeypatch.setattr(app_module.spotify_client, "call_api", fake_call_api)

    response = client.get("/api/me/player/recently-played")

    assert response.status_code == 200
