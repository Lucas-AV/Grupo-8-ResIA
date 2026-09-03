# Spotify API Explorer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Flask dev tool (`spotify_explorer/`) that lets the group call the Spotify Web API directly — catalog data (search, tracks, artists, audio features/analysis, recommendations) via Client Credentials, and the logged-in user's own data (top tracks/artists, saved tracks, recently played) via Authorization Code login — and see the raw JSON/status codes back, including the 403s from endpoints Spotify restricts for new apps.

**Architecture:** Two small backend modules with no Flask dependency of their own (`spotify_client.py` for app-only calls, `user_auth.py` for the user OAuth flow using `flask.session`), a Flask app (`app.py`) that wires both into `/api/*` JSON routes, and a single-page vanilla-JS frontend (5 tabs) that calls those routes via `fetch` and renders the raw JSON.

**Tech Stack:** Python 3.12, Flask, `requests`, `python-dotenv`, `pytest` + `unittest.mock` for tests, vanilla JS/CSS for the frontend (no build step).

**Spec:** `docs/superpowers/specs/2026-09-01-spotify-api-explorer-design.md`

---

## Task 1: Project scaffolding

**Files:**
- Create: `spotify_explorer/requirements.txt`
- Create: `spotify_explorer/.env.example`
- Modify: `.gitignore`

- [ ] **Step 1: Create the requirements file**

```
flask>=3.0,<4
requests>=2.31,<3
python-dotenv>=1.0,<2
```

- [ ] **Step 2: Create the env example file**

```
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
SPOTIFY_REDIRECT_URI=http://127.0.0.1:5000/callback
FLASK_SECRET_KEY=change-me-to-a-random-string
```

- [ ] **Step 3: Gitignore the real .env**

Add this line to the end of `.gitignore` (repo root):

```
spotify_explorer/.env
```

- [ ] **Step 4: Install dependencies**

Run: `pip install -r spotify_explorer/requirements.txt -r requirements.txt`
Expected: installs cleanly (root `requirements.txt` already has `pytest`, needed for the tests in later tasks).

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/requirements.txt spotify_explorer/.env.example .gitignore
git commit -m "chore: scaffold spotify_explorer project"
```

---

## Task 2: `spotify_client.py` — app-only token and generic API call

**Files:**
- Create: `spotify_explorer/spotify_client.py`
- Test: `spotify_explorer/test_spotify_client.py`

- [ ] **Step 1: Write the failing tests**

```python
# spotify_explorer/test_spotify_client.py
import time
from unittest.mock import Mock, patch

import spotify_client


def setup_function():
    spotify_client._token_cache["access_token"] = None
    spotify_client._token_cache["expires_at"] = 0


@patch("spotify_client.requests.post")
def test_get_app_token_requests_new_token_when_none_cached(mock_post):
    mock_post.return_value = Mock(
        json=lambda: {"access_token": "abc123", "expires_in": 3600},
        raise_for_status=lambda: None,
    )

    token = spotify_client.get_app_token("client-id", "client-secret")

    assert token == "abc123"
    mock_post.assert_called_once()


@patch("spotify_client.requests.post")
def test_get_app_token_reuses_cached_token_before_expiry(mock_post):
    spotify_client._token_cache["access_token"] = "cached-token"
    spotify_client._token_cache["expires_at"] = time.time() + 1000

    token = spotify_client.get_app_token("client-id", "client-secret")

    assert token == "cached-token"
    mock_post.assert_not_called()


@patch("spotify_client.requests.post")
def test_get_app_token_refreshes_after_expiry(mock_post):
    spotify_client._token_cache["access_token"] = "old-token"
    spotify_client._token_cache["expires_at"] = time.time() - 10
    mock_post.return_value = Mock(
        json=lambda: {"access_token": "new-token", "expires_in": 3600},
        raise_for_status=lambda: None,
    )

    token = spotify_client.get_app_token("client-id", "client-secret")

    assert token == "new-token"
    mock_post.assert_called_once()


@patch("spotify_client.requests.get")
def test_call_api_returns_json_and_status_on_success(mock_get):
    mock_get.return_value = Mock(status_code=200, json=lambda: {"id": "track1"}, headers={})

    body, status = spotify_client.call_api("/tracks/track1", "user-or-app-token")

    assert status == 200
    assert body == {"id": "track1"}
    args, kwargs = mock_get.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer user-or-app-token"


@patch("spotify_client.requests.get")
def test_call_api_returns_error_body_and_status_on_failure(mock_get):
    mock_get.return_value = Mock(
        status_code=403,
        json=lambda: {"error": {"status": 403, "message": "Forbidden"}},
        headers={},
    )

    body, status = spotify_client.call_api("/audio-features/track1", "token")

    assert status == 403
    assert body["error"]["message"] == "Forbidden"


@patch("spotify_client.requests.get")
def test_call_api_includes_retry_after_on_429(mock_get):
    mock_get.return_value = Mock(
        status_code=429,
        json=lambda: {"error": {"status": 429, "message": "rate limited"}},
        headers={"Retry-After": "5"},
    )

    body, status = spotify_client.call_api("/search", "token")

    assert status == 429
    assert body["retry_after_seconds"] == "5"
    assert body["error"]["message"] == "rate limited"


@patch("spotify_client.call_api")
@patch("spotify_client.get_app_token", return_value="fake-app-token")
def test_api_get_uses_app_token_and_delegates_to_call_api(mock_get_token, mock_call_api):
    mock_call_api.return_value = ({"tracks": []}, 200)

    body, status = spotify_client.api_get(
        "/search", "client-id", "client-secret", params={"q": "test"}
    )

    assert (body, status) == ({"tracks": []}, 200)
    mock_get_token.assert_called_once_with("client-id", "client-secret")
    mock_call_api.assert_called_once_with("/search", "fake-app-token", params={"q": "test"})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd spotify_explorer && pytest test_spotify_client.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'spotify_client'`

- [ ] **Step 3: Write the implementation**

```python
# spotify_explorer/spotify_client.py
import base64
import time

import requests

TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"

_token_cache = {"access_token": None, "expires_at": 0}


def get_app_token(client_id, client_secret):
    if _token_cache["access_token"] and _token_cache["expires_at"] > time.time():
        return _token_cache["access_token"]

    credentials = f"{client_id}:{client_secret}".encode("utf-8")
    encoded = base64.b64encode(credentials).decode("utf-8")
    response = requests.post(
        TOKEN_URL,
        headers={"Authorization": f"Basic {encoded}"},
        data={"grant_type": "client_credentials"},
    )
    response.raise_for_status()
    payload = response.json()
    _token_cache["access_token"] = payload["access_token"]
    _token_cache["expires_at"] = time.time() + payload["expires_in"] - 30
    return _token_cache["access_token"]


def call_api(path, token, params=None):
    response = requests.get(
        f"{API_BASE}{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params or {},
    )
    body = response.json()
    retry_after = response.headers.get("Retry-After")
    if response.status_code == 429 and retry_after is not None:
        body["retry_after_seconds"] = retry_after
    return body, response.status_code


def api_get(path, client_id, client_secret, params=None):
    token = get_app_token(client_id, client_secret)
    return call_api(path, token, params=params)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd spotify_explorer && pytest test_spotify_client.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/spotify_client.py spotify_explorer/test_spotify_client.py
git commit -m "feat: add app-only Spotify token cache and generic API caller"
```

---

## Task 3: `user_auth.py` — user OAuth login, code exchange, token refresh

**Files:**
- Create: `spotify_explorer/user_auth.py`
- Test: `spotify_explorer/test_user_auth.py`

- [ ] **Step 1: Write the failing tests**

```python
# spotify_explorer/test_user_auth.py
import time
from unittest.mock import Mock, patch

import pytest
from flask import Flask, session

import user_auth


@pytest.fixture
def app():
    flask_app = Flask(__name__)
    flask_app.secret_key = "test-secret"
    return flask_app


def test_get_login_url_contains_client_id_scope_redirect_and_state(app):
    with app.test_request_context():
        url = user_auth.get_login_url("client-id", "http://127.0.0.1:5000/callback")

        assert "client_id=client-id" in url
        assert "user-top-read" in url
        assert "user-library-read" in url
        assert "user-read-recently-played" in url
        assert "redirect_uri=" in url
        assert "state=" in url
        assert session["oauth_state"] in url


@patch("user_auth.requests.post")
def test_exchange_code_stores_tokens_in_session(mock_post, app):
    mock_post.return_value = Mock(
        status_code=200,
        json=lambda: {"access_token": "at", "refresh_token": "rt", "expires_in": 3600},
        raise_for_status=lambda: None,
    )

    with app.test_request_context():
        session["oauth_state"] = "abc"

        user_auth.exchange_code(
            "code123", "abc", "client-id", "client-secret",
            "http://127.0.0.1:5000/callback",
        )

        assert session["user_access_token"] == "at"
        assert session["user_refresh_token"] == "rt"


def test_exchange_code_rejects_mismatched_state(app):
    with app.test_request_context():
        session["oauth_state"] = "expected"

        with pytest.raises(ValueError):
            user_auth.exchange_code(
                "code123", "wrong-state", "client-id", "client-secret",
                "http://127.0.0.1:5000/callback",
            )


def test_get_valid_user_token_returns_cached_when_not_expired(app):
    with app.test_request_context():
        session["user_access_token"] = "cached-at"
        session["user_token_expires_at"] = time.time() + 1000

        token = user_auth.get_valid_user_token("client-id", "client-secret")

        assert token == "cached-at"


@patch("user_auth.requests.post")
def test_get_valid_user_token_refreshes_when_expired(mock_post, app):
    mock_post.return_value = Mock(
        status_code=200,
        json=lambda: {"access_token": "new-at", "expires_in": 3600},
    )

    with app.test_request_context():
        session["user_access_token"] = "old-at"
        session["user_refresh_token"] = "rt"
        session["user_token_expires_at"] = time.time() - 10

        token = user_auth.get_valid_user_token("client-id", "client-secret")

        assert token == "new-at"


@patch("user_auth.requests.post")
def test_get_valid_user_token_clears_session_when_refresh_fails(mock_post, app):
    mock_post.return_value = Mock(status_code=400, json=lambda: {"error": "invalid_grant"})

    with app.test_request_context():
        session["user_access_token"] = "old-at"
        session["user_refresh_token"] = "revoked-rt"
        session["user_token_expires_at"] = time.time() - 10

        with pytest.raises(user_auth.NotLoggedInError):
            user_auth.get_valid_user_token("client-id", "client-secret")

        assert "user_access_token" not in session


def test_get_valid_user_token_raises_when_not_logged_in(app):
    with app.test_request_context():
        with pytest.raises(user_auth.NotLoggedInError):
            user_auth.get_valid_user_token("client-id", "client-secret")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd spotify_explorer && pytest test_user_auth.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'user_auth'`

- [ ] **Step 3: Write the implementation**

```python
# spotify_explorer/user_auth.py
import base64
import secrets
import time
from urllib.parse import urlencode

import requests
from flask import session

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
SCOPES = "user-top-read user-library-read user-read-recently-played"


class NotLoggedInError(Exception):
    pass


def get_login_url(client_id, redirect_uri):
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": SCOPES,
        "state": state,
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def _basic_auth_header(client_id, client_secret):
    credentials = f"{client_id}:{client_secret}".encode("utf-8")
    return base64.b64encode(credentials).decode("utf-8")


def exchange_code(code, state, client_id, client_secret, redirect_uri):
    if state != session.get("oauth_state"):
        raise ValueError("state inválido — possível CSRF, tente logar novamente")

    response = requests.post(
        TOKEN_URL,
        headers={"Authorization": f"Basic {_basic_auth_header(client_id, client_secret)}"},
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        },
    )
    response.raise_for_status()
    payload = response.json()
    session["user_access_token"] = payload["access_token"]
    session["user_refresh_token"] = payload["refresh_token"]
    session["user_token_expires_at"] = time.time() + payload["expires_in"] - 30


def get_valid_user_token(client_id, client_secret):
    if "user_access_token" not in session:
        raise NotLoggedInError("faça login primeiro em /login")

    if session["user_token_expires_at"] > time.time():
        return session["user_access_token"]

    response = requests.post(
        TOKEN_URL,
        headers={"Authorization": f"Basic {_basic_auth_header(client_id, client_secret)}"},
        data={
            "grant_type": "refresh_token",
            "refresh_token": session["user_refresh_token"],
        },
    )
    if response.status_code != 200:
        session.clear()
        raise NotLoggedInError("sessão expirada, faça login novamente")

    payload = response.json()
    session["user_access_token"] = payload["access_token"]
    session["user_token_expires_at"] = time.time() + payload["expires_in"] - 30
    if "refresh_token" in payload:
        session["user_refresh_token"] = payload["refresh_token"]
    return session["user_access_token"]


def logout():
    session.clear()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd spotify_explorer && pytest test_user_auth.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/user_auth.py spotify_explorer/test_user_auth.py
git commit -m "feat: add Spotify user OAuth login, code exchange, and token refresh"
```

---

## Task 4: `app.py` — app factory, index route, catalog routes (search/track/audio-features/audio-analysis)

**Files:**
- Create: `spotify_explorer/app.py`
- Create: `spotify_explorer/conftest.py`
- Test: `spotify_explorer/test_app.py`

- [ ] **Step 1: Write the failing tests**

```python
# spotify_explorer/conftest.py
import pytest

import app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "client-id")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:5000/callback")
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret")
    flask_app = app_module.create_app()
    flask_app.config["TESTING"] = True
    return flask_app.test_client()
```

```python
# spotify_explorer/test_app.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd spotify_explorer && pytest test_app.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: Write the implementation**

```python
# spotify_explorer/app.py
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for

import spotify_client
import user_auth

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-not-for-production")
    app.config["SPOTIFY_CLIENT_ID"] = os.environ.get("SPOTIFY_CLIENT_ID", "")
    app.config["SPOTIFY_CLIENT_SECRET"] = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
    app.config["SPOTIFY_REDIRECT_URI"] = os.environ.get(
        "SPOTIFY_REDIRECT_URI", "http://127.0.0.1:5000/callback"
    )
    register_routes(app)
    return app


def register_routes(app):
    @app.route("/")
    def index():
        missing_credentials = not (
            app.config["SPOTIFY_CLIENT_ID"] and app.config["SPOTIFY_CLIENT_SECRET"]
        )
        return render_template(
            "index.html",
            missing_credentials=missing_credentials,
            auth_error=request.args.get("auth_error"),
        )

    @app.route("/api/search", methods=["POST"])
    def search():
        data = request.get_json(force=True)
        body, status = spotify_client.api_get(
            "/search",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
            params={
                "q": data.get("q", ""),
                "type": data.get("type", "track"),
                "limit": data.get("limit", 10),
            },
        )
        return jsonify(body), status

    @app.route("/api/track/<track_id>")
    def track(track_id):
        body, status = spotify_client.api_get(
            f"/tracks/{track_id}",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
        )
        return jsonify(body), status

    @app.route("/api/audio-features/<track_id>")
    def audio_features(track_id):
        body, status = spotify_client.api_get(
            f"/audio-features/{track_id}",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
        )
        return jsonify(body), status

    @app.route("/api/audio-analysis/<track_id>")
    def audio_analysis(track_id):
        body, status = spotify_client.api_get(
            f"/audio-analysis/{track_id}",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
        )
        return jsonify(body), status


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(debug=True)
```

Note: `templates/index.html` doesn't exist yet — `test_index_returns_200` will fail at Step 4 until Task 9 creates it. Create a minimal placeholder now so this task's tests pass in isolation:

```html
<!-- spotify_explorer/templates/index.html -->
<!doctype html>
<html lang="pt-br">
<head><meta charset="utf-8"><title>Spotify API Explorer</title></head>
<body><h1>Spotify API Explorer</h1></body>
</html>
```

Task 9 replaces this placeholder with the full UI.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd spotify_explorer && pytest test_app.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/app.py spotify_explorer/conftest.py spotify_explorer/test_app.py spotify_explorer/templates/index.html
git commit -m "feat: add Flask app with catalog routes (search, track, audio-features, audio-analysis)"
```

---

## Task 5: `app.py` — artist routes

**Files:**
- Modify: `spotify_explorer/app.py`
- Modify: `spotify_explorer/test_app.py`

- [ ] **Step 1: Add the failing tests**

Append to `spotify_explorer/test_app.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd spotify_explorer && pytest test_app.py -v`
Expected: FAIL with 404s (routes not defined)

- [ ] **Step 3: Add the routes**

Add inside `register_routes(app)` in `spotify_explorer/app.py`, after the `audio_analysis` route:

```python
    @app.route("/api/artist/<artist_id>")
    def artist(artist_id):
        body, status = spotify_client.api_get(
            f"/artists/{artist_id}",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
        )
        return jsonify(body), status

    @app.route("/api/artist/<artist_id>/top-tracks")
    def artist_top_tracks(artist_id):
        body, status = spotify_client.api_get(
            f"/artists/{artist_id}/top-tracks",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
            params={"market": request.args.get("market", "US")},
        )
        return jsonify(body), status

    @app.route("/api/artist/<artist_id>/albums")
    def artist_albums(artist_id):
        body, status = spotify_client.api_get(
            f"/artists/{artist_id}/albums",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
        )
        return jsonify(body), status

    @app.route("/api/artist/<artist_id>/related-artists")
    def artist_related_artists(artist_id):
        body, status = spotify_client.api_get(
            f"/artists/{artist_id}/related-artists",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
        )
        return jsonify(body), status
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd spotify_explorer && pytest test_app.py -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/app.py spotify_explorer/test_app.py
git commit -m "feat: add artist routes (artist, top-tracks, albums, related-artists)"
```

---

## Task 6: `app.py` — recommendations route

**Files:**
- Modify: `spotify_explorer/app.py`
- Modify: `spotify_explorer/test_app.py`

- [ ] **Step 1: Add the failing test**

Append to `spotify_explorer/test_app.py`:

```python
def test_recommendations_forwards_query_params(client, monkeypatch):
    def fake_api_get(path, client_id, client_secret, params=None):
        assert path == "/recommendations"
        assert params == {"seed_genres": "pop", "target_energy": "0.8"}
        return {"tracks": []}, 200

    monkeypatch.setattr(app_module.spotify_client, "api_get", fake_api_get)

    response = client.get("/api/recommendations?seed_genres=pop&target_energy=0.8")

    assert response.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd spotify_explorer && pytest test_app.py -v -k recommendations`
Expected: FAIL with 404 (route not defined)

- [ ] **Step 3: Add the route**

Add inside `register_routes(app)` in `spotify_explorer/app.py`, after the artist routes. Query params are forwarded as-is — `seed_tracks`/`seed_artists`/`seed_genres` and any `target_*`/`min_*`/`max_*` param the caller sends, since this endpoint is meant to be explored raw:

```python
    @app.route("/api/recommendations")
    def recommendations():
        body, status = spotify_client.api_get(
            "/recommendations",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
            params=request.args.to_dict(),
        )
        return jsonify(body), status
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd spotify_explorer && pytest test_app.py -v`
Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/app.py spotify_explorer/test_app.py
git commit -m "feat: add recommendations route"
```

---

## Task 7: `app.py` — user login/callback/logout and `/api/me`

**Files:**
- Modify: `spotify_explorer/app.py`
- Create: `spotify_explorer/test_app_auth.py`

- [ ] **Step 1: Write the failing tests**

```python
# spotify_explorer/test_app_auth.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd spotify_explorer && pytest test_app_auth.py -v`
Expected: FAIL with 404s (routes not defined)

- [ ] **Step 3: Add the routes**

Add inside `register_routes(app)` in `spotify_explorer/app.py`, after the `recommendations` route:

```python
    @app.route("/login")
    def login():
        return redirect(
            user_auth.get_login_url(
                app.config["SPOTIFY_CLIENT_ID"], app.config["SPOTIFY_REDIRECT_URI"]
            )
        )

    @app.route("/callback")
    def callback():
        error = request.args.get("error")
        if error:
            return redirect(url_for("index", auth_error=error))

        try:
            user_auth.exchange_code(
                request.args.get("code"),
                request.args.get("state"),
                app.config["SPOTIFY_CLIENT_ID"],
                app.config["SPOTIFY_CLIENT_SECRET"],
                app.config["SPOTIFY_REDIRECT_URI"],
            )
        except ValueError as exc:
            return redirect(url_for("index", auth_error=str(exc)))

        return redirect(url_for("index"))

    @app.route("/logout")
    def logout():
        user_auth.logout()
        return redirect(url_for("index"))

    @app.route("/api/me")
    def me():
        try:
            token = user_auth.get_valid_user_token(
                app.config["SPOTIFY_CLIENT_ID"], app.config["SPOTIFY_CLIENT_SECRET"]
            )
        except user_auth.NotLoggedInError as exc:
            return jsonify({"error": str(exc)}), 401

        body, status = spotify_client.call_api("/me", token)
        return jsonify(body), status
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd spotify_explorer && pytest test_app_auth.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/app.py spotify_explorer/test_app_auth.py
git commit -m "feat: add user login/callback/logout and /api/me routes"
```

---

## Task 8: `app.py` — user data routes (top tracks/artists, saved tracks, recently played)

**Files:**
- Modify: `spotify_explorer/app.py`
- Modify: `spotify_explorer/test_app_auth.py`

- [ ] **Step 1: Add the failing tests**

Append to `spotify_explorer/test_app_auth.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd spotify_explorer && pytest test_app_auth.py -v`
Expected: FAIL with 404s (routes not defined)

- [ ] **Step 3: Add the routes**

Add inside `register_routes(app)` in `spotify_explorer/app.py`, after the `/api/me` route:

```python
    def _user_data_route(path, params=None):
        try:
            token = user_auth.get_valid_user_token(
                app.config["SPOTIFY_CLIENT_ID"], app.config["SPOTIFY_CLIENT_SECRET"]
            )
        except user_auth.NotLoggedInError as exc:
            return jsonify({"error": str(exc)}), 401

        body, status = spotify_client.call_api(path, token, params=params)
        return jsonify(body), status

    @app.route("/api/me/top/tracks")
    def top_tracks():
        return _user_data_route(
            "/me/top/tracks",
            params={
                "time_range": request.args.get("time_range", "medium_term"),
                "limit": request.args.get("limit", "20"),
            },
        )

    @app.route("/api/me/top/artists")
    def top_artists():
        return _user_data_route(
            "/me/top/artists",
            params={
                "time_range": request.args.get("time_range", "medium_term"),
                "limit": request.args.get("limit", "20"),
            },
        )

    @app.route("/api/me/tracks")
    def saved_tracks():
        return _user_data_route(
            "/me/tracks",
            params={
                "limit": request.args.get("limit", "20"),
                "offset": request.args.get("offset", "0"),
            },
        )

    @app.route("/api/me/player/recently-played")
    def recently_played():
        return _user_data_route(
            "/me/player/recently-played",
            params={"limit": request.args.get("limit", "20")},
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd spotify_explorer && pytest test_app_auth.py -v`
Expected: 13 passed

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/app.py spotify_explorer/test_app_auth.py
git commit -m "feat: add user data routes (top tracks/artists, saved tracks, recently played)"
```

---

## Task 9: Frontend shell — markup, styles, and JSON rendering core

**Files:**
- Modify: `spotify_explorer/templates/index.html` (replace placeholder from Task 4)
- Create: `spotify_explorer/static/style.css`
- Create: `spotify_explorer/static/app.js`

No backend logic here — this is manually verified by running the server and clicking around, since the project has no JS test runner.

- [ ] **Step 1: Write the full page markup**

```html
<!-- spotify_explorer/templates/index.html -->
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Spotify API Explorer</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
  <header>
    <h1>Spotify API Explorer</h1>
    <div id="user-status"></div>
  </header>

  {% if missing_credentials %}
  <div class="banner banner-error">
    SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET não configurados. Copie
    <code>.env.example</code> para <code>.env</code> e preencha com um app criado no
    <a href="https://developer.spotify.com/dashboard" target="_blank" rel="noopener">Spotify Developer Dashboard</a>.
  </div>
  {% endif %}

  {% if auth_error %}
  <div class="banner banner-error">Erro no login: {{ auth_error }}</div>
  {% endif %}

  <nav class="tabs">
    <button class="tab-button active" data-tab="tab-search">Search</button>
    <button class="tab-button" data-tab="tab-track">Track &amp; Audio</button>
    <button class="tab-button" data-tab="tab-artist">Artist</button>
    <button class="tab-button" data-tab="tab-recommendations">Recommendations</button>
    <button class="tab-button" data-tab="tab-me">Meus dados</button>
  </nav>

  <section id="tab-search" class="tab-panel active">
    <form id="search-form">
      <label>Query <input type="text" name="q" required></label>
      <label>Type
        <select name="type">
          <option value="track">track</option>
          <option value="artist">artist</option>
          <option value="album">album</option>
        </select>
      </label>
      <label>Limit <input type="number" name="limit" value="10" min="1" max="50"></label>
      <button type="submit">Buscar</button>
    </form>
    <p class="status" id="search-status"></p>
    <div class="result" id="search-result"></div>
  </section>

  <section id="tab-track" class="tab-panel">
    <form id="track-form">
      <label>Track ID <input type="text" name="track_id" required placeholder="ex: 11dFghVXANMlKmJXsNCbNl"></label>
      <button type="submit">Buscar track + audio-features + audio-analysis</button>
    </form>
    <p class="status" id="track-status"></p>
    <div class="result" id="track-result"></div>
  </section>

  <section id="tab-artist" class="tab-panel">
    <form id="artist-form">
      <label>Artist ID <input type="text" name="artist_id" required placeholder="ex: 0TnOYISbd1XYRBk9myaseg"></label>
      <button type="submit">Buscar artist + top-tracks + albums + related-artists</button>
    </form>
    <p class="status" id="artist-status"></p>
    <div class="result" id="artist-result"></div>
  </section>

  <section id="tab-recommendations" class="tab-panel">
    <form id="recommendations-form">
      <label>Seed genres (csv) <input type="text" name="seed_genres" placeholder="pop,rock"></label>
      <label>Seed tracks (csv) <input type="text" name="seed_tracks"></label>
      <label>Seed artists (csv) <input type="text" name="seed_artists"></label>
      <label>Target energy (0-1) <input type="number" name="target_energy" step="0.1" min="0" max="1"></label>
      <label>Target valence (0-1) <input type="number" name="target_valence" step="0.1" min="0" max="1"></label>
      <button type="submit">Buscar recomendações</button>
    </form>
    <p class="status" id="recommendations-status"></p>
    <div class="result" id="recommendations-result"></div>
  </section>

  <section id="tab-me" class="tab-panel">
    <div id="me-logged-out">
      <p>Nenhum usuário conectado.</p>
      <a class="button" href="/login">Conectar Spotify</a>
    </div>
    <div id="me-logged-in" hidden>
      <p id="me-profile"></p>
      <a class="button" href="/logout">Desconectar</a>

      <fieldset>
        <legend>Top tracks / artists</legend>
        <form id="top-form">
          <label>Time range
            <select name="time_range">
              <option value="short_term">short_term (~4 semanas)</option>
              <option value="medium_term" selected>medium_term (~6 meses)</option>
              <option value="long_term">long_term (vários anos)</option>
            </select>
          </label>
          <button type="submit" data-target="tracks">Top tracks</button>
          <button type="submit" data-target="artists">Top artists</button>
        </form>
        <p class="status" id="top-status"></p>
        <div class="result" id="top-result"></div>
      </fieldset>

      <fieldset>
        <legend>Faixas curtidas</legend>
        <button type="button" id="saved-tracks-button">Buscar curtidas</button>
        <p class="status" id="saved-tracks-status"></p>
        <div class="result" id="saved-tracks-result"></div>
      </fieldset>

      <fieldset>
        <legend>Tocadas recentemente</legend>
        <button type="button" id="recently-played-button">Buscar recentes (máx. 50)</button>
        <p class="status" id="recently-played-status"></p>
        <div class="result" id="recently-played-result"></div>
      </fieldset>
    </div>
  </section>

  <script src="{{ url_for('static', filename='app.js') }}"></script>
</body>
</html>
```

- [ ] **Step 2: Write the stylesheet**

```css
/* spotify_explorer/static/style.css */
:root {
  color-scheme: light dark;
  --accent: #1db954;
  --border: #ccc;
  --error: #c0392b;
}

body {
  font-family: system-ui, sans-serif;
  margin: 0;
  padding: 1.5rem;
  max-width: 960px;
  margin-inline: auto;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.banner {
  padding: 0.75rem 1rem;
  border-radius: 6px;
  margin: 1rem 0;
}

.banner-error {
  background: color-mix(in srgb, var(--error) 15%, transparent);
  border: 1px solid var(--error);
}

.tabs {
  display: flex;
  gap: 0.5rem;
  border-bottom: 1px solid var(--border);
  margin: 1rem 0;
  flex-wrap: wrap;
}

.tab-button {
  padding: 0.5rem 1rem;
  border: none;
  background: none;
  cursor: pointer;
  border-bottom: 2px solid transparent;
}

.tab-button.active {
  border-bottom-color: var(--accent);
  font-weight: bold;
}

.tab-panel {
  display: none;
}

.tab-panel.active {
  display: block;
}

form {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: end;
}

label {
  display: flex;
  flex-direction: column;
  font-size: 0.85rem;
  gap: 0.25rem;
}

fieldset {
  margin-top: 1.5rem;
}

.button, button {
  cursor: pointer;
}

.status {
  font-family: monospace;
}

.status-ok {
  color: var(--accent);
}

.status-error {
  color: var(--error);
}

.result {
  background: color-mix(in srgb, currentColor 5%, transparent);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0.75rem;
  font-family: monospace;
  font-size: 0.85rem;
  overflow-x: auto;
}

.json-indent {
  margin-left: 1.25rem;
}

.json-key {
  opacity: 0.7;
}
```

- [ ] **Step 3: Write the JS core (tabs, JSON renderer, fetch helper)**

```javascript
// spotify_explorer/static/app.js

function initTabs() {
  document.querySelectorAll(".tab-button").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".tab-button").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      button.classList.add("active");
      document.getElementById(button.dataset.tab).classList.add("active");
    });
  });
}

function renderValue(value) {
  if (value === null || value === undefined) {
    return document.createTextNode("null");
  }
  if (Array.isArray(value)) {
    return renderContainer(value, "[", "]");
  }
  if (typeof value === "object") {
    return renderContainer(value, "{", "}");
  }
  return document.createTextNode(JSON.stringify(value));
}

function renderContainer(value, open, close) {
  const entries = Array.isArray(value) ? value.map((v, i) => [i, v]) : Object.entries(value);

  if (entries.length === 0) {
    const span = document.createElement("span");
    span.textContent = open + close;
    return span;
  }

  const details = document.createElement("details");
  details.open = true;
  const summary = document.createElement("summary");
  summary.textContent = `${open} ${entries.length} item(s) ${close}`;
  details.appendChild(summary);

  const list = document.createElement("div");
  list.className = "json-indent";
  entries.forEach(([key, val]) => {
    const row = document.createElement("div");
    const keySpan = document.createElement("span");
    keySpan.className = "json-key";
    keySpan.textContent = `${key}: `;
    row.appendChild(keySpan);
    row.appendChild(renderValue(val));
    list.appendChild(row);
  });
  details.appendChild(list);
  return details;
}

function renderJSON(container, data) {
  container.innerHTML = "";
  container.appendChild(renderValue(data));
}

async function callEndpoint(url, options, resultEl, statusEl) {
  statusEl.textContent = "Carregando...";
  statusEl.className = "status";
  try {
    const response = await fetch(url, options);
    const data = await response.json();
    statusEl.textContent = `HTTP ${response.status}`;
    statusEl.className = "status " + (response.ok ? "status-ok" : "status-error");
    renderJSON(resultEl, data);
    return { ok: response.ok, status: response.status, data };
  } catch (err) {
    statusEl.textContent = "Erro de rede";
    statusEl.className = "status status-error";
    resultEl.textContent = String(err);
    return { ok: false, status: 0, data: null };
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
});
```

- [ ] **Step 4: Manual verification**

Run: `cd spotify_explorer && python app.py`
Open `http://127.0.0.1:5000` in a browser.
Expected: page loads, 5 tabs visible, clicking each tab switches the visible panel, no console errors. If `.env` has no credentials yet, the missing-credentials banner shows.

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/templates/index.html spotify_explorer/static/style.css spotify_explorer/static/app.js
git commit -m "feat: add frontend shell with tabs and collapsible JSON renderer"
```

---

## Task 10: Frontend — wire Search / Track & Audio / Artist / Recommendations tabs

**Files:**
- Modify: `spotify_explorer/static/app.js`

- [ ] **Step 1: Add the form handlers**

Add to `spotify_explorer/static/app.js`, replacing the `DOMContentLoaded` listener at the bottom:

```javascript
function initSearchForm() {
  const form = document.getElementById("search-form");
  const resultEl = document.getElementById("search-result");
  const statusEl = document.getElementById("search-status");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    await callEndpoint(
      "/api/search",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          q: formData.get("q"),
          type: formData.get("type"),
          limit: Number(formData.get("limit")),
        }),
      },
      resultEl,
      statusEl
    );
  });
}

function initTrackForm() {
  const form = document.getElementById("track-form");
  const resultEl = document.getElementById("track-result");
  const statusEl = document.getElementById("track-status");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const trackId = new FormData(form).get("track_id");

    const [track, audioFeatures, audioAnalysis] = await Promise.all([
      fetch(`/api/track/${trackId}`).then((r) => r.json()),
      fetch(`/api/audio-features/${trackId}`).then((r) => r.json()),
      fetch(`/api/audio-analysis/${trackId}`).then((r) => r.json()),
    ]);

    statusEl.textContent = "3 chamadas concluídas (ver JSON por seção)";
    statusEl.className = "status status-ok";
    renderJSON(resultEl, { track, audio_features: audioFeatures, audio_analysis: audioAnalysis });
  });
}

function initArtistForm() {
  const form = document.getElementById("artist-form");
  const resultEl = document.getElementById("artist-result");
  const statusEl = document.getElementById("artist-status");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const artistId = new FormData(form).get("artist_id");

    const [artist, topTracks, albums, relatedArtists] = await Promise.all([
      fetch(`/api/artist/${artistId}`).then((r) => r.json()),
      fetch(`/api/artist/${artistId}/top-tracks`).then((r) => r.json()),
      fetch(`/api/artist/${artistId}/albums`).then((r) => r.json()),
      fetch(`/api/artist/${artistId}/related-artists`).then((r) => r.json()),
    ]);

    statusEl.textContent = "4 chamadas concluídas (ver JSON por seção)";
    statusEl.className = "status status-ok";
    renderJSON(resultEl, {
      artist,
      top_tracks: topTracks,
      albums,
      related_artists: relatedArtists,
    });
  });
}

function initRecommendationsForm() {
  const form = document.getElementById("recommendations-form");
  const resultEl = document.getElementById("recommendations-result");
  const statusEl = document.getElementById("recommendations-status");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    const params = new URLSearchParams();
    for (const [key, value] of formData.entries()) {
      if (value) params.set(key, value);
    }
    await callEndpoint(`/api/recommendations?${params}`, {}, resultEl, statusEl);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initSearchForm();
  initTrackForm();
  initArtistForm();
  initRecommendationsForm();
});
```

- [ ] **Step 2: Manual verification**

Fill in real `SPOTIFY_CLIENT_ID`/`SPOTIFY_CLIENT_SECRET` in `spotify_explorer/.env` (create a Client Credentials app at the Spotify Developer Dashboard if needed).
Run: `cd spotify_explorer && python app.py`
In the browser: search for a track by name in the Search tab → expect HTTP 200 and a JSON result with `tracks.items`. Copy a track ID from that result into the Track & Audio tab → expect track + audio-features + audio-analysis JSON (audio-features/audio-analysis may show HTTP 403 if the app isn't Extended Quota approved — that's expected and correct behavior per the spec, not a bug). Try the Artist and Recommendations tabs similarly.

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/static/app.js
git commit -m "feat: wire search, track, artist, and recommendations tabs to the backend"
```

---

## Task 11: Frontend — wire "Meus dados" tab (login, top tracks/artists, saved tracks, recently played)

**Files:**
- Modify: `spotify_explorer/static/app.js`

- [ ] **Step 1: Add the user-data handlers**

Add to `spotify_explorer/static/app.js`, above the final `DOMContentLoaded` listener:

```javascript
async function loadUserStatus() {
  const loggedOutEl = document.getElementById("me-logged-out");
  const loggedInEl = document.getElementById("me-logged-in");
  const profileEl = document.getElementById("me-profile");
  const headerStatusEl = document.getElementById("user-status");

  const response = await fetch("/api/me");
  if (!response.ok) {
    loggedOutEl.hidden = false;
    loggedInEl.hidden = true;
    headerStatusEl.textContent = "";
    return;
  }

  const profile = await response.json();
  loggedOutEl.hidden = true;
  loggedInEl.hidden = false;
  profileEl.textContent = `Logado como: ${profile.display_name || profile.id}`;
  headerStatusEl.textContent = profile.display_name || profile.id;
}

function initTopForm() {
  const form = document.getElementById("top-form");
  const resultEl = document.getElementById("top-result");
  const statusEl = document.getElementById("top-status");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const target = event.submitter.dataset.target;
    const timeRange = new FormData(form).get("time_range");
    const path = target === "artists" ? "/api/me/top/artists" : "/api/me/top/tracks";
    await callEndpoint(`${path}?time_range=${timeRange}`, {}, resultEl, statusEl);
  });
}

function initSavedTracksButton() {
  const button = document.getElementById("saved-tracks-button");
  const resultEl = document.getElementById("saved-tracks-result");
  const statusEl = document.getElementById("saved-tracks-status");

  button.addEventListener("click", async () => {
    await callEndpoint("/api/me/tracks", {}, resultEl, statusEl);
  });
}

function initRecentlyPlayedButton() {
  const button = document.getElementById("recently-played-button");
  const resultEl = document.getElementById("recently-played-result");
  const statusEl = document.getElementById("recently-played-status");

  button.addEventListener("click", async () => {
    await callEndpoint("/api/me/player/recently-played?limit=50", {}, resultEl, statusEl);
  });
}
```

- [ ] **Step 2: Wire it all up on load**

Replace the final `DOMContentLoaded` listener in `spotify_explorer/static/app.js`:

```javascript
document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initSearchForm();
  initTrackForm();
  initArtistForm();
  initRecommendationsForm();
  initTopForm();
  initSavedTracksButton();
  initRecentlyPlayedButton();
  loadUserStatus();
});
```

- [ ] **Step 3: Manual verification**

In the Spotify Developer Dashboard, add `http://127.0.0.1:5000/callback` as a Redirect URI on the app used for `SPOTIFY_CLIENT_ID`.
Run: `cd spotify_explorer && python app.py`
In the browser: open the "Meus dados" tab → click "Conectar Spotify" → log in with a real Spotify account → get redirected back → tab now shows your display name and "Desconectar". Click "Top tracks" for each `time_range` → expect HTTP 200 with track lists (or an empty list if the account has too little listening history for that window). Click "Buscar curtidas" and "Buscar recentes" → expect HTTP 200 with your saved tracks / recently played. Click "Desconectar" → tab reverts to the "Conectar Spotify" button.

- [ ] **Step 4: Commit**

```bash
git add spotify_explorer/static/app.js
git commit -m "feat: wire Meus dados tab (login, top tracks/artists, saved tracks, recently played)"
```

---

## Task 12: `README.md` — setup and smoke test checklist

**Files:**
- Create: `spotify_explorer/README.md`

- [ ] **Step 1: Write the README**

```markdown
# Spotify API Explorer

Dev tool interna do Grupo 8 pra explorar a Web API do Spotify: quais
endpoints existem, quais dados retornam, e quais restrições reais existem
hoje. Não faz parte do produto final — ver
`docs/superpowers/specs/2026-09-01-spotify-api-explorer-design.md` pro
design completo.

## Setup

1. Crie um app em https://developer.spotify.com/dashboard
2. Em "Redirect URIs" do app, adicione `http://127.0.0.1:5000/callback`
   (necessário mesmo se você só for usar as abas de catálogo, sem login)
3. Copie `.env.example` para `.env` dentro de `spotify_explorer/` e
   preencha `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` com os do seu
   app. Gere um valor aleatório para `FLASK_SECRET_KEY` (ex:
   `python -c "import secrets; print(secrets.token_hex(32))"`)
4. Instale as dependências:
   ```
   pip install -r requirements.txt -r spotify_explorer/requirements.txt
   ```
5. Rode:
   ```
   cd spotify_explorer
   python app.py
   ```
6. Abra `http://127.0.0.1:5000`

## Rodando os testes

```
cd spotify_explorer
pytest
```

Todos os testes usam `requests` mockado — nenhum bate na API real, então
não precisam de credenciais.

## O que cada aba faz

- **Search** — `GET /search` do catálogo (track/artist/album)
- **Track & Audio** — `GET /tracks/{id}`, `/audio-features/{id}`,
  `/audio-analysis/{id}`
- **Artist** — `GET /artists/{id}` + top-tracks + albums + related-artists
- **Recommendations** — `GET /recommendations` com seeds e parâmetros alvo
- **Meus dados** — requer login (Authorization Code Flow): top
  tracks/artists por `time_range`, faixas curtidas, tocadas recentemente

## Restrições conhecidas da API (não são bugs da ferramenta)

Desde nov/2024 apps novos sem "Extended Quota Mode" recebem 403 em
`audio-features`, `audio-analysis`, `recommendations` e
`related-artists`. A ferramenta mostra esse 403 como veio — é justamente
o dado que o grupo quer descobrir.

`/me/player/recently-played` devolve no máximo as últimas 50 faixas
tocadas — não é um histórico de 6 meses. Pra "mais ouvidas nos últimos ~6
meses", use a aba Meus dados com `time_range=medium_term`, que é um
ranking por frequência calculado pela Spotify, não uma lista cronológica.

## Checklist de smoke test manual

- [ ] App sobe sem `.env` preenchido e mostra o aviso de credenciais faltando
- [ ] Search retorna resultados reais pra uma query conhecida
- [ ] Track & Audio retorna a track; audio-features/audio-analysis
      retornam dado ou 403 (dependendo do nível de acesso do seu app)
- [ ] Artist retorna os 4 blocos de dados
- [ ] Recommendations retorna tracks (ou 403, mesma observação acima)
- [ ] Login funciona e volta pra `/` autenticado
- [ ] Top tracks/artists funciona nas 3 janelas de tempo
- [ ] Faixas curtidas e tocadas recentemente retornam dado real
- [ ] Logout funciona e volta ao estado deslogado
```

- [ ] **Step 2: Commit**

```bash
git add spotify_explorer/README.md
git commit -m "docs: add spotify_explorer setup and smoke test README"
```

---

## Task 13: Final verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full backend test suite**

Run: `cd spotify_explorer && pytest -v`
Expected: all tests pass (Tasks 2–8 combined: 7 + 7 + 5 + 4 + 1 + 7 + 6 = 37 tests)

- [ ] **Step 2: Confirm the rest of the repo's tests still pass**

Run: `pytest` (from repo root)
Expected: existing `tests/` suite still passes unchanged — this feature touches no files outside `spotify_explorer/` and `docs/superpowers/`.

- [ ] **Step 3: Walk the manual smoke test checklist**

Follow the checklist in `spotify_explorer/README.md` end to end with a real Spotify app (Client Credentials + a real user login). Note any endpoint that returns 403 due to Extended Quota restrictions — that's expected, not a failure, per the spec.

- [ ] **Step 4: Confirm working tree is clean**

Run: `git status`
Expected: nothing to commit, working tree clean, all work committed on `feature/spotify-api-explorer`.
