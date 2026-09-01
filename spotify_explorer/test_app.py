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
