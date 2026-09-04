# Spotify Playback Control + Related Playlist Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add real playback control (play/pause/next/previous/seek/volume/shuffle/repeat) and a "generate a related playlist from what's playing now" feature to the Spotify Explorer dev tool's Player tab — the first two features in this tool that write to the user's real Spotify account.

**Architecture:** `spotify_client.call_api` and `app.py`'s `_user_data_route` helper both grow optional `method`/`json_body` support, backward-compatible by construction (existing GET-only call sites and their test mocks are untouched). 8 new thin passthrough routes handle playback control; 1 new orchestration route (`/api/me/playlists/related`) does 3 sequential Spotify calls server-side (recommendations → create playlist → add tracks) and stops early with a real error if any step fails, so a failed recommendations call never leaves an empty orphaned playlist. `PlayerTab.vue` grows transport buttons, seek/volume sliders, shuffle/repeat toggles, and a "gerar playlist relacionada" button — all wired through a small shared `callControl` helper that always does exactly one `fetchPlayer()` refetch after a successful action (no polling).

**Tech Stack:** Flask + `requests` (backend), Vue 3 `<script setup>` (frontend). Backend gets real `pytest` coverage (this is new logic, not a passthrough tweak) — no new dependencies either side.

---

## Task 1: `spotify_client.call_api` gains `method`/`json_body` support

**Files:**
- Modify: `spotify_explorer/spotify_client.py:60-84`
- Test: `spotify_explorer/test_spotify_client.py`

- [ ] **Step 1: Write the failing tests**

Append to `spotify_explorer/test_spotify_client.py`:

```python
@patch("spotify_client.requests.request")
def test_call_api_uses_requests_request_for_non_get_methods(mock_request):
    mock_request.return_value = Mock(status_code=201, json=lambda: {"id": "playlist1"}, headers={})

    body, status = spotify_client.call_api(
        "/me/playlists", "token", method="POST", json_body={"name": "Test"}
    )

    assert status == 201
    assert body == {"id": "playlist1"}
    args, kwargs = mock_request.call_args
    assert args[0] == "POST"
    assert kwargs["json"] == {"name": "Test"}
    assert kwargs["headers"]["Authorization"] == "Bearer token"


@patch("spotify_client.requests.get")
def test_call_api_still_uses_requests_get_for_default_get_method(mock_get):
    mock_get.return_value = Mock(status_code=200, json=lambda: {"id": "track1"}, headers={})

    body, status = spotify_client.call_api("/tracks/track1", "token")

    assert status == 200
    mock_get.assert_called_once()


@patch("spotify_client.requests.request", side_effect=requests.exceptions.ConnectionError("boom"))
def test_call_api_returns_error_tuple_on_connection_error_for_non_get(mock_request):
    body, status = spotify_client.call_api("/me/playlists", "token", method="POST", json_body={})

    assert status == 502
    assert body["error"] == "connection_error"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd spotify_explorer && pytest test_spotify_client.py -k "non_get_methods or still_uses_requests_get or connection_error_for_non_get" -v`
Expected: FAIL — `call_api()` doesn't accept `method`/`json_body` kwargs yet (`TypeError`)

- [ ] **Step 3: Implement**

In `spotify_explorer/spotify_client.py`, replace `call_api` (lines 60-84):

```python
def call_api(path, token, params=None, method="GET", json_body=None):
    try:
        if method == "GET":
            response = requests.get(
                f"{API_BASE}{path}",
                headers={"Authorization": f"Bearer {token}"},
                params=params or {},
            )
        else:
            response = requests.request(
                method,
                f"{API_BASE}{path}",
                headers={"Authorization": f"Bearer {token}"},
                params=params or {},
                json=json_body,
            )
    except requests.exceptions.RequestException as exc:
        return {"error": "connection_error", "error_description": str(exc)}, 502

    if response.status_code == 204:
        return {}, 204

    try:
        body = response.json()
    except ValueError:
        return (
            {"error": "invalid_response", "error_description": "resposta da Spotify não é JSON"},
            response.status_code,
        )

    retry_after = response.headers.get("Retry-After")
    if response.status_code == 429 and retry_after is not None:
        body["retry_after_seconds"] = retry_after
    return body, response.status_code
```

The `GET` branch is byte-for-byte what the function already did — this is why every existing test (which mocks `spotify_client.requests.get`) keeps passing unchanged.

- [ ] **Step 4: Run tests to verify they pass, then run the full backend suite**

Run: `cd spotify_explorer && pytest -v`
Expected: PASS — all tests, old and new (this is the widest-blast-radius change in this plan; a full-suite run here, not just the new tests, is required)

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/spotify_client.py spotify_explorer/test_spotify_client.py
git commit -m "feat: add method/json_body support to spotify_client.call_api"
```

---

## Task 2: Add `user-modify-playback-state` scope

**Files:**
- Modify: `spotify_explorer/user_auth.py:11-15`
- Test: `spotify_explorer/test_user_auth.py`

- [ ] **Step 1: Update the failing assertion**

In `spotify_explorer/test_user_auth.py`, replace `test_get_login_url_contains_client_id_scope_redirect_and_state`:

```python
def test_get_login_url_contains_client_id_scope_redirect_and_state(app):
    with app.test_request_context():
        url = user_auth.get_login_url("client-id", "http://127.0.0.1:5000/callback")

        assert "client_id=client-id" in url
        assert "user-top-read" in url
        assert "user-library-read" in url
        assert "user-read-recently-played" in url
        assert "user-read-playback-state" in url
        assert "user-read-currently-playing" in url
        assert "user-follow-read" in url
        assert "playlist-read-private" in url
        assert "user-modify-playback-state" in url
        assert "redirect_uri=" in url
        assert "state=" in url
        assert session["oauth_state"] in url
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd spotify_explorer && pytest test_user_auth.py::test_get_login_url_contains_client_id_scope_redirect_and_state -v`
Expected: FAIL — `assert "user-modify-playback-state" in url` fails

- [ ] **Step 3: Add the scope**

In `spotify_explorer/user_auth.py`, replace `SCOPES` (lines 11-15):

```python
SCOPES = (
    "user-top-read user-library-read user-read-recently-played "
    "user-read-playback-state user-read-currently-playing "
    "user-follow-read playlist-read-private user-modify-playback-state"
)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd spotify_explorer && pytest test_user_auth.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/user_auth.py spotify_explorer/test_user_auth.py
git commit -m "feat: add user-modify-playback-state OAuth scope"
```

---

## Task 3: `_user_data_route` gains conditional `method`/`json_body`, plus `/api/me/player/play` and `/api/me/player/pause`

**Files:**
- Modify: `spotify_explorer/app.py:207-217` (the `_user_data_route` helper), plus 2 new routes after `my_playlists()` (line 281)
- Test: `spotify_explorer/test_app_auth.py`

- [ ] **Step 1: Write the failing tests**

Append to `spotify_explorer/test_app_auth.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd spotify_explorer && pytest test_app_auth.py -k "player_play or player_pause" -v`
Expected: FAIL with `404 Not Found` (routes don't exist yet)

- [ ] **Step 3: Extend `_user_data_route` and add the two routes**

In `spotify_explorer/app.py`, replace `_user_data_route` (lines 207-217):

```python
    def _user_data_route(path, params=None, method="GET", json_body=None):
        try:
            token = user_auth.get_valid_user_token(
                app.config["SPOTIFY_CLIENT_ID"], app.config["SPOTIFY_CLIENT_SECRET"]
            )
        except user_auth.NotLoggedInError as exc:
            return jsonify({"error": str(exc)}), 401

        kwargs = {"params": params}
        if method != "GET":
            kwargs["method"] = method
        if json_body is not None:
            kwargs["json_body"] = json_body
        body, status = spotify_client.call_api(path, token, **kwargs)
        return jsonify(body), status
```

The conditional `kwargs` dict is essential: every existing route that calls `_user_data_route` (`top_tracks`, `saved_tracks`, `recently_played`, `player`, `player_queue`, `following`, `my_playlists`, etc.) never passes `method`/`json_body`, so they keep calling `spotify_client.call_api(path, token, params=params)` exactly as before — meaning every existing test's `fake_call_api(path, token, params=None)` mock (11+ of them across this file) keeps working completely unchanged. Only routes that explicitly pass a non-`"GET"` `method` (the new ones in this plan) trigger the extra kwargs.

Then add, after `my_playlists()` (after line 281, before `if __name__ ==`):

```python
    @app.route("/api/me/player/play", methods=["POST"])
    def player_play():
        return _user_data_route("/me/player/play", method="PUT")

    @app.route("/api/me/player/pause", methods=["POST"])
    def player_pause():
        return _user_data_route("/me/player/pause", method="PUT")
```

- [ ] **Step 4: Run tests to verify they pass, then run the full backend suite**

Run: `cd spotify_explorer && pytest -v`
Expected: PASS — all tests, old and new (confirms the conditional-kwargs change didn't break any existing `_user_data_route` consumer's test)

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/app.py spotify_explorer/test_app_auth.py
git commit -m "feat: add /api/me/player/play and /api/me/player/pause routes"
```

---

## Task 4: Add `/api/me/player/next` and `/api/me/player/previous`

**Files:**
- Modify: `spotify_explorer/app.py` (after `player_pause()`)
- Test: `spotify_explorer/test_app_auth.py`

- [ ] **Step 1: Write the failing tests**

Append to `spotify_explorer/test_app_auth.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd spotify_explorer && pytest test_app_auth.py -k "player_next or player_previous" -v`
Expected: FAIL with `404 Not Found`

- [ ] **Step 3: Add the routes**

In `spotify_explorer/app.py`, add after `player_pause()`:

```python
    @app.route("/api/me/player/next", methods=["POST"])
    def player_next():
        return _user_data_route("/me/player/next", method="POST")

    @app.route("/api/me/player/previous", methods=["POST"])
    def player_previous():
        return _user_data_route("/me/player/previous", method="POST")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd spotify_explorer && pytest test_app_auth.py -k "player_next or player_previous" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/app.py spotify_explorer/test_app_auth.py
git commit -m "feat: add /api/me/player/next and /api/me/player/previous routes"
```

---

## Task 5: Add `/api/me/player/seek` and `/api/me/player/volume`

**Files:**
- Modify: `spotify_explorer/app.py` (after `player_previous()`)
- Test: `spotify_explorer/test_app_auth.py`

- [ ] **Step 1: Write the failing tests**

Append to `spotify_explorer/test_app_auth.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd spotify_explorer && pytest test_app_auth.py -k "player_seek or player_volume" -v`
Expected: FAIL with `404 Not Found`

- [ ] **Step 3: Add the routes**

In `spotify_explorer/app.py`, add after `player_previous()`:

```python
    @app.route("/api/me/player/seek", methods=["POST"])
    def player_seek():
        return _user_data_route(
            "/me/player/seek",
            params={"position_ms": request.args.get("position_ms", "0")},
            method="PUT",
        )

    @app.route("/api/me/player/volume", methods=["POST"])
    def player_volume():
        return _user_data_route(
            "/me/player/volume",
            params={"volume_percent": request.args.get("volume_percent", "50")},
            method="PUT",
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd spotify_explorer && pytest test_app_auth.py -k "player_seek or player_volume" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/app.py spotify_explorer/test_app_auth.py
git commit -m "feat: add /api/me/player/seek and /api/me/player/volume routes"
```

---

## Task 6: Add `/api/me/player/shuffle` and `/api/me/player/repeat`

**Files:**
- Modify: `spotify_explorer/app.py` (after `player_volume()`)
- Test: `spotify_explorer/test_app_auth.py`

- [ ] **Step 1: Write the failing tests**

Append to `spotify_explorer/test_app_auth.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd spotify_explorer && pytest test_app_auth.py -k "player_shuffle or player_repeat" -v`
Expected: FAIL with `404 Not Found`

- [ ] **Step 3: Add the routes**

In `spotify_explorer/app.py`, add after `player_volume()`:

```python
    @app.route("/api/me/player/shuffle", methods=["POST"])
    def player_shuffle():
        return _user_data_route(
            "/me/player/shuffle",
            params={"state": request.args.get("state", "false")},
            method="PUT",
        )

    @app.route("/api/me/player/repeat", methods=["POST"])
    def player_repeat():
        return _user_data_route(
            "/me/player/repeat",
            params={"state": request.args.get("state", "off")},
            method="PUT",
        )
```

- [ ] **Step 4: Run tests to verify they pass, then run the full backend suite**

Run: `cd spotify_explorer && pytest -v`
Expected: PASS — all tests (this completes all 8 playback-control routes; a full-suite run confirms nothing regressed)

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/app.py spotify_explorer/test_app_auth.py
git commit -m "feat: add /api/me/player/shuffle and /api/me/player/repeat routes"
```

---

## Task 7: Add `/api/me/playlists/related` orchestration route

**Files:**
- Modify: `spotify_explorer/app.py` (imports at top, plus 1 new route after `player_repeat()`)
- Test: `spotify_explorer/test_app_auth.py`

- [ ] **Step 1: Write the failing tests**

Append to `spotify_explorer/test_app_auth.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd spotify_explorer && pytest test_app_auth.py -k "create_related_playlist" -v`
Expected: FAIL with `404 Not Found`

- [ ] **Step 3: Add the import and the route**

In `spotify_explorer/app.py`, add to the imports at the top of the file (after `import os`, before `from urllib.parse import urlencode`):

```python
from datetime import date
```

Then add the route after `player_repeat()`:

```python
    @app.route("/api/me/playlists/related", methods=["POST"])
    def create_related_playlist():
        data = request.get_json(silent=True) or {}
        track_id = data.get("track_id")
        track_name = data.get("track_name", "")
        if not track_id:
            return jsonify({"error": "missing_track_id"}), 400

        try:
            token = user_auth.get_valid_user_token(
                app.config["SPOTIFY_CLIENT_ID"], app.config["SPOTIFY_CLIENT_SECRET"]
            )
        except user_auth.NotLoggedInError as exc:
            return jsonify({"error": str(exc)}), 401

        rec_body, rec_status = spotify_client.call_api(
            "/recommendations", token, params={"seed_tracks": track_id, "limit": "20"}
        )
        if rec_status != 200 or not rec_body.get("tracks"):
            return jsonify({"step": "recommendations", "error": rec_body}), rec_status

        uris = [t["uri"] for t in rec_body["tracks"]]
        playlist_name = f"Relacionadas com {track_name} — {date.today().isoformat()}"

        create_body, create_status = spotify_client.call_api(
            "/me/playlists",
            token,
            method="POST",
            json_body={
                "name": playlist_name,
                "public": False,
                "description": "Gerado automaticamente pelo Spotify Explorer",
            },
        )
        if create_status not in (200, 201):
            return jsonify({"step": "create_playlist", "error": create_body}), create_status

        playlist_id = create_body["id"]
        add_body, add_status = spotify_client.call_api(
            f"/playlists/{playlist_id}/items", token, method="POST", json_body={"uris": uris}
        )
        if add_status not in (200, 201):
            return jsonify({"step": "add_items", "playlist": create_body, "error": add_body}), add_status

        return jsonify({"playlist": create_body, "added_tracks": len(uris)}), 200
```

- [ ] **Step 4: Run tests to verify they pass, then run the full backend suite**

Run: `cd spotify_explorer && pytest -v`
Expected: PASS — all tests. This completes all backend work in this plan.

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/app.py spotify_explorer/test_app_auth.py
git commit -m "feat: add /api/me/playlists/related orchestration route"
```

---

## Task 8: `PlayerTab.vue` — play/pause/next/previous buttons

**Files:**
- Modify: `spotify_explorer/frontend/src/tabs/PlayerTab.vue`

- [ ] **Step 1: Replace the full file**

```vue
<script setup>
import { computed, reactive } from "vue";
import { fetchJSON } from "../composables/useApi.js";
import { useAuthStatus } from "../composables/useAuthStatus.js";
import { trackSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import TrackPreview from "../components/previews/TrackPreview.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const { state: authState } = useAuthStatus();
const status = reactive({ text: "", className: "status", loading: false });
const result = reactive({ data: null });

const nowPlaying = computed(() => result.data?.player?.item ?? null);
const isPlaying = computed(() => result.data?.player?.is_playing ?? false);

const queueItems = computed(() => {
  const items = result.data?.queue?.queue;
  if (!Array.isArray(items)) return [];
  return items.map(trackSummary).filter((item) => item !== null);
});

function formatDuration(ms) {
  if (!ms) return "";
  const totalSeconds = Math.round(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

async function fetchPlayer() {
  status.loading = true;
  status.text = "Carregando...";
  status.className = "status";

  const [player, queue] = await Promise.all([
    fetchJSON("/api/me/player"),
    fetchJSON("/api/me/player/queue"),
  ]);

  status.loading = false;
  const allOk = player.ok && queue.ok;
  const statuses = [player, queue]
    .map((r) => (r.status === 0 ? "erro de rede" : r.status))
    .join(", ");
  status.text = `HTTP ${statuses}`;
  status.className = "status " + (allOk ? "status-ok" : "status-error");
  result.data = { player: player.data, queue: queue.data };
}

async function callControl(action, params = {}) {
  const query = new URLSearchParams(params).toString();
  const url = query ? `/api/me/player/${action}?${query}` : `/api/me/player/${action}`;
  await fetchJSON(url, { method: "POST" });
  await fetchPlayer();
}

function togglePlayPause() {
  callControl(isPlaying.value ? "pause" : "play");
}
</script>

<template>
  <section>
    <h2>Player</h2>
    <div v-if="!authState.loggedIn">
      <p>Nenhum usuário conectado.</p>
      <a class="btn" href="/login">Conectar Spotify</a>
    </div>
    <div v-else>
      <button type="button" class="btn" @click="fetchPlayer">Atualizar</button>
      <button type="button" class="btn btn-secondary" @click="callControl('previous')">⏮ Anterior</button>
      <button type="button" class="btn btn-secondary" @click="togglePlayPause">
        {{ isPlaying ? "⏸ Pausar" : "▶ Tocar" }}
      </button>
      <button type="button" class="btn btn-secondary" @click="callControl('next')">⏭ Próxima</button>
      <ResultPanel
        :status="status"
        :data="result.data"
        empty-hint="Clique em Atualizar pra ver o que está tocando"
      >
        <template #preview>
          <div v-if="nowPlaying">
            <TrackPreview :track="nowPlaying" />
            <div class="audio-feature-bar">
              <span>Progresso</span>
              <div class="audio-feature-track">
                <div
                  class="audio-feature-fill"
                  :style="{ width: `${(result.data.player.progress_ms / nowPlaying.duration_ms) * 100}%` }"
                ></div>
              </div>
              <span>
                {{ formatDuration(result.data.player.progress_ms) }} /
                {{ formatDuration(nowPlaying.duration_ms) }}
              </span>
            </div>
            <p v-if="result.data.player.device">
              Dispositivo: {{ result.data.player.device.name }} ({{ result.data.player.device.type }})
              — volume {{ result.data.player.device.volume_percent }}%
            </p>
            <p>
              Shuffle: {{ result.data.player.shuffle_state ? "ligado" : "desligado" }}
              — Repeat: {{ result.data.player.repeat_state }}
            </p>
          </div>
          <p v-else>Nada tocando no momento.</p>
          <div v-if="queueItems.length">
            <h3>Fila</h3>
            <div v-for="(item, i) in queueItems" :key="i">
              <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" :preview-url="item.previewUrl" />
            </div>
          </div>
        </template>
      </ResultPanel>
    </div>
  </section>
</template>
```

The only changes vs. the current file: `isPlaying` computed, `callControl`/`togglePlayPause` functions, and the 3 new buttons before `ResultPanel`. Everything else (`nowPlaying`, `queueItems`, `formatDuration`, `fetchPlayer`, the whole template body inside `ResultPanel`) is unchanged.

- [ ] **Step 2: Verify the build still succeeds**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/PlayerTab.vue
git commit -m "feat: add play/pause/next/previous controls to Player tab"
```

---

## Task 9: `PlayerTab.vue` — seek and volume sliders

**Files:**
- Modify: `spotify_explorer/frontend/src/tabs/PlayerTab.vue`

- [ ] **Step 1: Add the two sliders**

In `spotify_explorer/frontend/src/tabs/PlayerTab.vue`, inside the `v-if="nowPlaying"` block, add two new blocks right after the existing progress `<div class="audio-feature-bar">...</div>` block (the one showing "Progresso") and before the `<p v-if="result.data.player.device">` line:

```html
            <div class="audio-feature-bar">
              <span>Seek</span>
              <input
                type="range"
                min="0"
                :max="nowPlaying.duration_ms"
                :value="result.data.player.progress_ms"
                @change="callControl('seek', { position_ms: $event.target.value })"
              >
            </div>
            <div v-if="result.data.player.device" class="audio-feature-bar">
              <span>Volume</span>
              <input
                type="range"
                min="0"
                max="100"
                :value="result.data.player.device.volume_percent"
                @change="callControl('volume', { volume_percent: $event.target.value })"
              >
            </div>
```

No script changes needed — `callControl` already handles arbitrary `params`. The `@change` event (not `@input`) means the API call only fires when the user releases the slider, not on every drag tick.

- [ ] **Step 2: Verify the build still succeeds**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/PlayerTab.vue
git commit -m "feat: add seek and volume sliders to Player tab"
```

---

## Task 10: `PlayerTab.vue` — shuffle and repeat controls

**Files:**
- Modify: `spotify_explorer/frontend/src/tabs/PlayerTab.vue`

- [ ] **Step 1: Add `cycleRepeat` to the script**

In `spotify_explorer/frontend/src/tabs/PlayerTab.vue`, add after the `togglePlayPause` function:

```js
const REPEAT_STATES = ["off", "context", "track"];

function cycleRepeat() {
  const current = result.data.player.repeat_state;
  const currentIndex = REPEAT_STATES.indexOf(current);
  const next = REPEAT_STATES[(currentIndex + 1) % REPEAT_STATES.length];
  callControl("repeat", { state: next });
}
```

- [ ] **Step 2: Replace the static shuffle/repeat line with interactive buttons**

Replace:

```html
            <p>
              Shuffle: {{ result.data.player.shuffle_state ? "ligado" : "desligado" }}
              — Repeat: {{ result.data.player.repeat_state }}
            </p>
```

with:

```html
            <button
              type="button"
              class="btn btn-secondary"
              @click="callControl('shuffle', { state: !result.data.player.shuffle_state })"
            >
              Shuffle: {{ result.data.player.shuffle_state ? "ligado" : "desligado" }}
            </button>
            <button type="button" class="btn btn-secondary" @click="cycleRepeat">
              Repeat: {{ result.data.player.repeat_state }}
            </button>
```

`{ state: !result.data.player.shuffle_state }` passes a JS boolean into `callControl`'s `params` object; `URLSearchParams` (used inside `callControl`) stringifies booleans to the literal strings `"true"`/`"false"`, which is exactly the string format Spotify's `shuffle` endpoint expects for its `state` query param.

- [ ] **Step 3: Verify the build still succeeds**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds

- [ ] **Step 4: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/PlayerTab.vue
git commit -m "feat: add shuffle and repeat controls to Player tab"
```

---

## Task 11: `PlayerTab.vue` — "Gerar playlist relacionada" button

**Files:**
- Modify: `spotify_explorer/frontend/src/tabs/PlayerTab.vue`

- [ ] **Step 1: Add the related-playlist state and function**

In `spotify_explorer/frontend/src/tabs/PlayerTab.vue`, add after `cycleRepeat`:

```js
const relatedPlaylist = reactive({ status: "", data: null, error: null });

async function generateRelatedPlaylist() {
  relatedPlaylist.status = "loading";
  relatedPlaylist.data = null;
  relatedPlaylist.error = null;

  const outcome = await fetchJSON("/api/me/playlists/related", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ track_id: nowPlaying.value.id, track_name: nowPlaying.value.name }),
  });

  if (outcome.ok) {
    relatedPlaylist.status = "ok";
    relatedPlaylist.data = outcome.data;
  } else {
    relatedPlaylist.status = "error";
    relatedPlaylist.error = outcome.data;
  }
}
```

(Named the local variable `outcome`, not `result`, to avoid shadowing the file's existing top-level `result` reactive object.)

- [ ] **Step 2: Add the button and result display to the template**

In `spotify_explorer/frontend/src/tabs/PlayerTab.vue`, inside the `v-if="nowPlaying"` block, add right after the `<TrackPreview :track="nowPlaying" />` line:

```html
            <button
              type="button"
              class="btn"
              :disabled="relatedPlaylist.status === 'loading'"
              @click="generateRelatedPlaylist"
            >
              Gerar playlist relacionada
            </button>
            <p v-if="relatedPlaylist.status === 'ok'">
              Playlist criada — {{ relatedPlaylist.data.added_tracks }} faixas.
              <a :href="relatedPlaylist.data.playlist.external_urls.spotify" target="_blank" rel="noopener">
                Abrir no Spotify
              </a>
            </p>
            <p v-else-if="relatedPlaylist.status === 'error'" class="status status-error">
              Erro ({{ relatedPlaylist.error?.step }}): {{ JSON.stringify(relatedPlaylist.error?.error) }}
            </p>
```

- [ ] **Step 3: Verify the build still succeeds**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds

- [ ] **Step 4: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/PlayerTab.vue
git commit -m "feat: add related-playlist generation button to Player tab"
```

---

## Task 12: Update `spotify_explorer/README.md`

**Files:**
- Modify: `spotify_explorer/README.md`

- [ ] **Step 1: Add the re-login callout for the new scope**

In `spotify_explorer/README.md`, the existing re-login callout (the blockquote right after the numbered setup list, starting "Se você já tinha uma sessão logada de antes da Fase 2") needs its scope list extended. Find that blockquote and replace it:

```markdown
> **Se você já tinha uma sessão logada de antes:** os escopos do OAuth
> mudaram (`user-read-playback-state`, `user-read-currently-playing`,
> `user-follow-read`, `playlist-read-private`,
> `user-modify-playback-state`). Deslogue e logue de novo — a Spotify
> só pede consentimento dos escopos novos numa nova autorização; um
> token antigo não os tem.
```

- [ ] **Step 2: Update the Player bullet in "O que cada aba faz"**

Replace the existing Player bullet:

```markdown
- **Player** — `GET /me/player` (o que tá tocando, dispositivo,
  progresso) + `GET /me/player/queue` (fila) — só leitura, sem
  controles de reprodução. Requer login.
```

with:

```markdown
- **Player** — `GET /me/player` (o que tá tocando, dispositivo,
  progresso) + `GET /me/player/queue` (fila), mais controles reais de
  reprodução (play/pause/next/previous/seek/volume/shuffle/repeat) via
  `PUT`/`POST /me/player/*` — a primeira parte da ferramenta que
  escreve de verdade na conta do usuário. Também gera uma playlist
  privada com faixas relacionadas à que está tocando agora
  (`GET /recommendations` + `POST /me/playlists` + `POST
  /playlists/{id}/items`). Requer login.
```

- [ ] **Step 3: Add a new restriction note**

In "## Restrições conhecidas da API (não são bugs da ferramenta)", add after the existing fev/2026 paragraph about Artist/Playlist:

```markdown
Os controles de reprodução (`/me/player/play`, `/pause`, `/next`,
`/previous`, `/seek`, `/volume`, `/shuffle`, `/repeat`) precisam de um
dispositivo Spotify ativo (app aberto em algum lugar logado na mesma
conta) — sem isso a Spotify devolve 404
(`NO_ACTIVE_DEVICE`/`NO_PREV_TRACK` etc.). Também exigem conta
Premium — contas free recebem 403 (`PREMIUM_REQUIRED`). A geração de
playlist relacionada depende de `GET /recommendations`, que já é um
403 conhecido desde nov/2024 pra apps sem Extended Quota Mode — o
botão provavelmente vai mostrar esse erro em vez de criar a playlist,
o que já é o comportamento esperado (documentado acima).
```

- [ ] **Step 4: Add to the smoke-test checklist**

In "## Checklist de smoke test manual", add:

```markdown
- [ ] Play/pause/next/previous mudam o estado real no dispositivo
      ativo (ou mostram 404/403 se não houver dispositivo ativo/conta
      não for Premium)
- [ ] Seek e volume só disparam a chamada ao soltar o slider, não a
      cada movimento
- [ ] Shuffle e repeat alternam estado e refletem isso após o refetch
      automático
- [ ] Gerar playlist relacionada cria uma playlist privada de verdade
      (ou mostra o erro real do passo que falhou — recommendations,
      create_playlist ou add_items)
```

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/README.md
git commit -m "docs: document playback control and related-playlist features"
```

---

## Task 13: Final verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full backend test suite**

Run: `cd spotify_explorer && pytest -v`
Expected: all tests pass, including every new test added across Tasks 1-7

- [ ] **Step 2: Run the full frontend build**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds with no errors

- [ ] **Step 3: Confirm no other backend route's behavior changed**

Run: `git diff main -- spotify_explorer/app.py spotify_explorer/spotify_client.py`
Expected: every hunk is either a new route/function, or the two intentional, narrowly-scoped signature extensions (`call_api`, `_user_data_route`) described in Tasks 1 and 3 — nothing else in either file should show a diff

- [ ] **Step 4: Manual smoke test (requires a real, active Spotify session)**

Start the backend (`cd spotify_explorer && python app.py`) and frontend dev server (`cd spotify_explorer/frontend && npm run dev`), open `http://127.0.0.1:5173`, log out and log back in (new scope), open a Spotify client on any device so there's an active device, then walk the 4 new checklist items added to `spotify_explorer/README.md` in Task 12. This is the first feature in this tool that writes to a real account — treat any unexpected side effect (wrong track skipped, volume changed unexpectedly, a playlist actually created) as a real finding to report, not just a checkbox to tick.
