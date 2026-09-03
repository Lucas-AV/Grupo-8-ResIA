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


def test_callback_redirects_to_configured_frontend_url(client, monkeypatch):
    def fake_exchange_code(code, state, client_id, client_secret, redirect_uri):
        pass

    monkeypatch.setattr(app_module.user_auth, "exchange_code", fake_exchange_code)
    client.application.config["FRONTEND_URL"] = "http://127.0.0.1:5173"

    response = client.get("/callback?code=abc&state=xyz")

    assert response.status_code == 302
    assert response.location == "http://127.0.0.1:5173"


def test_logout_redirects_to_configured_frontend_url(client, monkeypatch):
    monkeypatch.setattr(app_module.user_auth, "logout", lambda: None)
    client.application.config["FRONTEND_URL"] = "http://127.0.0.1:5173"

    response = client.get("/logout")

    assert response.status_code == 302
    assert response.location == "http://127.0.0.1:5173"


def test_player_calls_correct_path(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )

    def fake_call_api(path, token, params=None):
        assert path == "/me/player"
        return {"is_playing": True}, 200

    monkeypatch.setattr(app_module.spotify_client, "call_api", fake_call_api)

    response = client.get("/api/me/player")

    assert response.status_code == 200


def test_player_returns_204_when_nothing_playing(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )
    monkeypatch.setattr(app_module.spotify_client, "call_api", lambda path, token, params=None: ({}, 204))

    response = client.get("/api/me/player")

    assert response.status_code == 204


def test_player_requires_login(client, monkeypatch):
    def fake_get_valid_user_token(client_id, client_secret):
        raise app_module.user_auth.NotLoggedInError("faça login primeiro em /login")

    monkeypatch.setattr(app_module.user_auth, "get_valid_user_token", fake_get_valid_user_token)

    response = client.get("/api/me/player")

    assert response.status_code == 401


def test_player_queue_calls_correct_path(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )

    def fake_call_api(path, token, params=None):
        assert path == "/me/player/queue"
        return {"currently_playing": None, "queue": []}, 200

    monkeypatch.setattr(app_module.spotify_client, "call_api", fake_call_api)

    response = client.get("/api/me/player/queue")

    assert response.status_code == 200


def test_following_uses_type_artist_and_limit(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )

    def fake_call_api(path, token, params=None):
        assert path == "/me/following"
        assert params == {"type": "artist", "limit": "10"}
        return {"artists": {"items": []}}, 200

    monkeypatch.setattr(app_module.spotify_client, "call_api", fake_call_api)

    response = client.get("/api/me/following?limit=10")

    assert response.status_code == 200


def test_following_defaults_limit_to_20(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )

    def fake_call_api(path, token, params=None):
        assert params["limit"] == "20"
        return {"artists": {"items": []}}, 200

    monkeypatch.setattr(app_module.spotify_client, "call_api", fake_call_api)

    response = client.get("/api/me/following")

    assert response.status_code == 200


def test_my_playlists_calls_correct_path(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )

    def fake_call_api(path, token, params=None):
        assert path == "/me/playlists"
        assert params == {"limit": "20", "offset": "0"}
        return {"items": []}, 200

    monkeypatch.setattr(app_module.spotify_client, "call_api", fake_call_api)

    response = client.get("/api/me/playlists")

    assert response.status_code == 200


def test_player_play_calls_correct_path_and_method(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )

    def fake_call_api(path, token, params=None, method="GET", json_body=None):
        assert path == "/me/player/play"
        assert method == "PUT"
        return {}, 204

    monkeypatch.setattr(app_module.spotify_client, "call_api", fake_call_api)

    response = client.post("/api/me/player/play")

    assert response.status_code == 204


def test_player_play_requires_login(client, monkeypatch):
    def fake_get_valid_user_token(client_id, client_secret):
        raise app_module.user_auth.NotLoggedInError("faça login primeiro em /login")

    monkeypatch.setattr(app_module.user_auth, "get_valid_user_token", fake_get_valid_user_token)

    response = client.post("/api/me/player/play")

    assert response.status_code == 401


def test_player_pause_calls_correct_path_and_method(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )

    def fake_call_api(path, token, params=None, method="GET", json_body=None):
        assert path == "/me/player/pause"
        assert method == "PUT"
        return {}, 204

    monkeypatch.setattr(app_module.spotify_client, "call_api", fake_call_api)

    response = client.post("/api/me/player/pause")

    assert response.status_code == 204


def test_player_next_calls_correct_path_and_method(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )

    def fake_call_api(path, token, params=None, method="GET", json_body=None):
        assert path == "/me/player/next"
        assert method == "POST"
        return {}, 204

    monkeypatch.setattr(app_module.spotify_client, "call_api", fake_call_api)

    response = client.post("/api/me/player/next")

    assert response.status_code == 204


def test_player_previous_calls_correct_path_and_method(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )

    def fake_call_api(path, token, params=None, method="GET", json_body=None):
        assert path == "/me/player/previous"
        assert method == "POST"
        return {}, 204

    monkeypatch.setattr(app_module.spotify_client, "call_api", fake_call_api)

    response = client.post("/api/me/player/previous")

    assert response.status_code == 204


def test_player_seek_uses_position_ms_param(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )

    def fake_call_api(path, token, params=None, method="GET", json_body=None):
        assert path == "/me/player/seek"
        assert method == "PUT"
        assert params == {"position_ms": "30000"}
        return {}, 204

    monkeypatch.setattr(app_module.spotify_client, "call_api", fake_call_api)

    response = client.post("/api/me/player/seek?position_ms=30000")

    assert response.status_code == 204


def test_player_volume_uses_volume_percent_param(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )

    def fake_call_api(path, token, params=None, method="GET", json_body=None):
        assert path == "/me/player/volume"
        assert method == "PUT"
        assert params == {"volume_percent": "80"}
        return {}, 204

    monkeypatch.setattr(app_module.spotify_client, "call_api", fake_call_api)

    response = client.post("/api/me/player/volume?volume_percent=80")

    assert response.status_code == 204


def test_player_shuffle_uses_state_param(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )

    def fake_call_api(path, token, params=None, method="GET", json_body=None):
        assert path == "/me/player/shuffle"
        assert method == "PUT"
        assert params == {"state": "true"}
        return {}, 204

    monkeypatch.setattr(app_module.spotify_client, "call_api", fake_call_api)

    response = client.post("/api/me/player/shuffle?state=true")

    assert response.status_code == 204


def test_player_repeat_uses_state_param(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )

    def fake_call_api(path, token, params=None, method="GET", json_body=None):
        assert path == "/me/player/repeat"
        assert method == "PUT"
        assert params == {"state": "track"}
        return {}, 204

    monkeypatch.setattr(app_module.spotify_client, "call_api", fake_call_api)

    response = client.post("/api/me/player/repeat?state=track")

    assert response.status_code == 204


def test_create_related_playlist_happy_path(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )

    calls = []

    def fake_call_api(path, token, params=None, method="GET", json_body=None):
        calls.append(path)
        if path == "/recommendations":
            assert params == {"seed_tracks": "track123", "limit": "20"}
            return {"tracks": [{"uri": "spotify:track:a"}, {"uri": "spotify:track:b"}]}, 200
        if path == "/me/playlists":
            assert method == "POST"
            assert json_body["public"] is False
            return (
                {
                    "id": "playlist1",
                    "external_urls": {"spotify": "https://open.spotify.com/playlist/playlist1"},
                },
                201,
            )
        if path == "/playlists/playlist1/items":
            assert method == "POST"
            assert json_body == {"uris": ["spotify:track:a", "spotify:track:b"]}
            return {"snapshot_id": "abc"}, 201
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(app_module.spotify_client, "call_api", fake_call_api)

    response = client.post(
        "/api/me/playlists/related",
        json={"track_id": "track123", "track_name": "Test Track"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["added_tracks"] == 2
    assert data["playlist"]["id"] == "playlist1"
    assert calls == ["/recommendations", "/me/playlists", "/playlists/playlist1/items"]


def test_create_related_playlist_stops_if_recommendations_fails(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )

    calls = []

    def fake_call_api(path, token, params=None, method="GET", json_body=None):
        calls.append(path)
        return {"error": {"status": 403, "message": "forbidden"}}, 403

    monkeypatch.setattr(app_module.spotify_client, "call_api", fake_call_api)

    response = client.post(
        "/api/me/playlists/related",
        json={"track_id": "track123", "track_name": "Test Track"},
    )

    assert response.status_code == 403
    data = response.get_json()
    assert data["step"] == "recommendations"
    assert calls == ["/recommendations"]


def test_create_related_playlist_stops_if_playlist_creation_fails(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )

    calls = []

    def fake_call_api(path, token, params=None, method="GET", json_body=None):
        calls.append(path)
        if path == "/recommendations":
            return {"tracks": [{"uri": "spotify:track:a"}]}, 200
        if path == "/me/playlists":
            return {"error": {"status": 403, "message": "forbidden"}}, 403
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(app_module.spotify_client, "call_api", fake_call_api)

    response = client.post(
        "/api/me/playlists/related",
        json={"track_id": "track123", "track_name": "Test Track"},
    )

    assert response.status_code == 403
    data = response.get_json()
    assert data["step"] == "create_playlist"
    assert calls == ["/recommendations", "/me/playlists"]


def test_create_related_playlist_requires_track_id(client, monkeypatch):
    monkeypatch.setattr(
        app_module.user_auth, "get_valid_user_token", lambda cid, secret: "user-token"
    )

    response = client.post("/api/me/playlists/related", json={})

    assert response.status_code == 400


def test_create_related_playlist_requires_login(client, monkeypatch):
    def fake_get_valid_user_token(client_id, client_secret):
        raise app_module.user_auth.NotLoggedInError("faça login primeiro em /login")

    monkeypatch.setattr(app_module.user_auth, "get_valid_user_token", fake_get_valid_user_token)

    response = client.post(
        "/api/me/playlists/related", json={"track_id": "track123", "track_name": "Test"}
    )

    assert response.status_code == 401
