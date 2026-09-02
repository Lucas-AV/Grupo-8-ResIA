import app as app_module


def test_index_returns_200(client):
    response = client.get("/")

    assert response.status_code == 200


def test_search_calls_spotify_search_endpoint(client, monkeypatch):
    def fake_api_get(path, client_id, client_secret, params=None):
        assert path == "/search"
        assert params == {"q": "test", "type": "track", "limit": 5}
        return {"tracks": {"items": []}}, 200

    monkeypatch.setattr(app_module.spotify_client, "api_get", fake_api_get)

    response = client.post("/api/search", json={"q": "test", "type": "track", "limit": 5})

    assert response.status_code == 200
    assert response.get_json() == {"tracks": {"items": []}}


def test_search_with_missing_body_does_not_crash(client, monkeypatch):
    def fake_api_get(path, client_id, client_secret, params=None):
        assert path == "/search"
        assert params == {"q": "", "type": "track", "limit": 10}
        return {"error": {"status": 400, "message": "No search query"}}, 400

    monkeypatch.setattr(app_module.spotify_client, "api_get", fake_api_get)

    response = client.post("/api/search")

    assert response.status_code == 400
    assert response.get_json()["error"]["message"] == "No search query"


def test_track_returns_spotify_status_code_on_error(client, monkeypatch):
    def fake_api_get(path, client_id, client_secret, params=None):
        assert path == "/tracks/bad-id"
        return {"error": {"status": 404, "message": "not found"}}, 404

    monkeypatch.setattr(app_module.spotify_client, "api_get", fake_api_get)

    response = client.get("/api/track/bad-id")

    assert response.status_code == 404
    assert response.get_json()["error"]["message"] == "not found"


def test_audio_features_calls_correct_path(client, monkeypatch):
    def fake_api_get(path, client_id, client_secret, params=None):
        assert path == "/audio-features/track1"
        return {"danceability": 0.5}, 200

    monkeypatch.setattr(app_module.spotify_client, "api_get", fake_api_get)

    response = client.get("/api/audio-features/track1")

    assert response.status_code == 200
    assert response.get_json() == {"danceability": 0.5}


def test_audio_analysis_calls_correct_path(client, monkeypatch):
    def fake_api_get(path, client_id, client_secret, params=None):
        assert path == "/audio-analysis/track1"
        return {"track": {}}, 200

    monkeypatch.setattr(app_module.spotify_client, "api_get", fake_api_get)

    response = client.get("/api/audio-analysis/track1")

    assert response.status_code == 200


def test_artist_calls_correct_path(client, monkeypatch):
    def fake_api_get(path, client_id, client_secret, params=None):
        assert path == "/artists/artist1"
        return {"name": "Test Artist"}, 200

    monkeypatch.setattr(app_module.spotify_client, "api_get", fake_api_get)

    response = client.get("/api/artist/artist1")

    assert response.status_code == 200
    assert response.get_json() == {"name": "Test Artist"}


def test_artist_top_tracks_calls_correct_path(client, monkeypatch):
    def fake_api_get(path, client_id, client_secret, params=None):
        assert path == "/artists/artist1/top-tracks"
        return {"tracks": []}, 200

    monkeypatch.setattr(app_module.spotify_client, "api_get", fake_api_get)

    response = client.get("/api/artist/artist1/top-tracks")

    assert response.status_code == 200


def test_artist_albums_calls_correct_path(client, monkeypatch):
    def fake_api_get(path, client_id, client_secret, params=None):
        assert path == "/artists/artist1/albums"
        return {"items": []}, 200

    monkeypatch.setattr(app_module.spotify_client, "api_get", fake_api_get)

    response = client.get("/api/artist/artist1/albums")

    assert response.status_code == 200


def test_artist_related_artists_calls_correct_path(client, monkeypatch):
    def fake_api_get(path, client_id, client_secret, params=None):
        assert path == "/artists/artist1/related-artists"
        return {"artists": []}, 200

    monkeypatch.setattr(app_module.spotify_client, "api_get", fake_api_get)

    response = client.get("/api/artist/artist1/related-artists")

    assert response.status_code == 200


def test_recommendations_forwards_query_params(client, monkeypatch):
    def fake_api_get(path, client_id, client_secret, params=None):
        assert path == "/recommendations"
        assert params == {"seed_genres": "pop", "target_energy": "0.8"}
        return {"tracks": []}, 200

    monkeypatch.setattr(app_module.spotify_client, "api_get", fake_api_get)

    response = client.get("/api/recommendations?seed_genres=pop&target_energy=0.8")

    assert response.status_code == 200


def test_index_shows_build_instructions_when_frontend_not_built(client, tmp_path):
    client.application.config["FRONTEND_DIST_DIR"] = str(tmp_path / "does-not-exist")

    response = client.get("/")

    assert response.status_code == 200
    assert b"npm run build" in response.data


def test_index_serves_built_frontend_when_present(client, tmp_path):
    (tmp_path / "index.html").write_text("<html><body>built app</body></html>", encoding="utf-8")
    client.application.config["FRONTEND_DIST_DIR"] = str(tmp_path)

    response = client.get("/")

    assert response.status_code == 200
    assert b"built app" in response.data


def test_config_reports_missing_credentials(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "")
    monkeypatch.setenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:5000/callback")
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret")
    flask_app = app_module.create_app()
    test_client = flask_app.test_client()

    response = test_client.get("/api/config")

    assert response.status_code == 200
    assert response.get_json() == {"missing_credentials": True}


def test_config_reports_credentials_present(client):
    response = client.get("/api/config")

    assert response.status_code == 200
    assert response.get_json() == {"missing_credentials": False}
