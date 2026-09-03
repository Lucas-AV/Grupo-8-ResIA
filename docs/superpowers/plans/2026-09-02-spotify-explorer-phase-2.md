# Spotify Explorer — Fase 2 (Player, Seguindo, Minhas Playlists) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 3 new tabs to the Spotify API Explorer (Player, Seguindo, Minhas Playlists) covering the OAuth-scoped endpoints deferred from Fase 1, plus cross-tab navigation so clicking an artist/playlist in these new lists jumps to the existing Artist/Playlist tabs.

**Architecture:** Same patterns as every prior phase — Flask routes delegating to `_user_data_route` (Authorization Code Flow helper already in `app.py`), Vue tabs following the `useApi`/`ResultPanel`/preview-card conventions. One new piece of infrastructure: a module-scoped `useTabNavigation.js` composable so a tab can tell `App.vue` "switch to tab X with this ID" without prop-drilling.

**Tech Stack:** Flask + `requests` (backend, unchanged), Vue 3 `<script setup>` + Vite (frontend, unchanged). No new dependencies.

---

## Task 1: Expand OAuth scopes

**Files:**
- Modify: `spotify_explorer/user_auth.py:11`
- Test: `spotify_explorer/test_user_auth.py:18-28`

- [ ] **Step 1: Update the failing assertions first**

Replace the test in `spotify_explorer/test_user_auth.py`:

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
        assert "redirect_uri=" in url
        assert "state=" in url
        assert session["oauth_state"] in url
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd spotify_explorer && pytest test_user_auth.py::test_get_login_url_contains_client_id_scope_redirect_and_state -v`
Expected: FAIL — `assert "user-read-playback-state" in url` fails (scope not present yet)

- [ ] **Step 3: Add the new scopes**

In `spotify_explorer/user_auth.py`, replace line 11:

```python
SCOPES = (
    "user-top-read user-library-read user-read-recently-played "
    "user-read-playback-state user-read-currently-playing "
    "user-follow-read playlist-read-private"
)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd spotify_explorer && pytest test_user_auth.py -v`
Expected: PASS (all tests in the file)

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/user_auth.py spotify_explorer/test_user_auth.py
git commit -m "feat: add phase 2 OAuth scopes (player, following, playlists)"
```

---

## Task 2: Fix 204 handling in `spotify_client.call_api`

Spotify returns **204 No Content** (empty body) from `/me/player` and
`/me/player/queue` when nothing is playing. `call_api` today calls
`response.json()` unconditionally, which raises `ValueError` on an
empty body and turns a legitimate "nothing playing" response into a
fake `invalid_response` error.

**Files:**
- Modify: `spotify_explorer/spotify_client.py:60-81`
- Test: `spotify_explorer/test_spotify_client.py`

- [ ] **Step 1: Write the failing test**

Append to `spotify_explorer/test_spotify_client.py`:

```python
@patch("spotify_client.requests.get")
def test_call_api_returns_empty_body_on_204(mock_get):
    mock_get.return_value = Mock(
        status_code=204, json=Mock(side_effect=ValueError("no body")), headers={}
    )

    body, status = spotify_client.call_api("/me/player", "token")

    assert status == 204
    assert body == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd spotify_explorer && pytest test_spotify_client.py::test_call_api_returns_empty_body_on_204 -v`
Expected: FAIL — `body["error"] == "invalid_response"` instead of `body == {}` (the `ValueError` from `json()` is caught by the existing generic handler, not treated as a valid 204)

- [ ] **Step 3: Add the 204 branch**

In `spotify_explorer/spotify_client.py`, modify `call_api` (lines 60-81):

```python
def call_api(path, token, params=None):
    try:
        response = requests.get(
            f"{API_BASE}{path}",
            headers={"Authorization": f"Bearer {token}"},
            params=params or {},
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

- [ ] **Step 4: Run test to verify it passes**

Run: `cd spotify_explorer && pytest test_spotify_client.py -v`
Expected: PASS (all tests in the file — confirms the 204 branch didn't break the existing non-JSON-body test, since that one still uses a non-204 status)

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/spotify_client.py spotify_explorer/test_spotify_client.py
git commit -m "fix: treat 204 No Content as a valid empty response, not an error"
```

---

## Task 3: Add `/api/me/player` and `/api/me/player/queue` routes

**Files:**
- Modify: `spotify_explorer/app.py:248-253` (after `recently_played`)
- Test: `spotify_explorer/test_app_auth.py`

- [ ] **Step 1: Write the failing tests**

Append to `spotify_explorer/test_app_auth.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd spotify_explorer && pytest test_app_auth.py -k "player" -v`
Expected: FAIL with `404 Not Found` (routes don't exist yet)

- [ ] **Step 3: Add the routes**

In `spotify_explorer/app.py`, add after `recently_played()` (after line 253, before `if __name__ ==`):

```python
    @app.route("/api/me/player")
    def player():
        return _user_data_route("/me/player")

    @app.route("/api/me/player/queue")
    def player_queue():
        return _user_data_route("/me/player/queue")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd spotify_explorer && pytest test_app_auth.py -k "player" -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/app.py spotify_explorer/test_app_auth.py
git commit -m "feat: add /api/me/player and /api/me/player/queue routes"
```

---

## Task 4: Add `/api/me/following` route

**Files:**
- Modify: `spotify_explorer/app.py` (after the routes added in Task 3)
- Test: `spotify_explorer/test_app_auth.py`

- [ ] **Step 1: Write the failing test**

Append to `spotify_explorer/test_app_auth.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd spotify_explorer && pytest test_app_auth.py -k "following" -v`
Expected: FAIL with `404 Not Found`

- [ ] **Step 3: Add the route**

In `spotify_explorer/app.py`, add after `player_queue()`:

```python
    @app.route("/api/me/following")
    def following():
        return _user_data_route(
            "/me/following",
            params={
                "type": "artist",
                "limit": request.args.get("limit", "20"),
            },
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd spotify_explorer && pytest test_app_auth.py -k "following" -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/app.py spotify_explorer/test_app_auth.py
git commit -m "feat: add /api/me/following route"
```

---

## Task 5: Add `/api/me/playlists` route

**Files:**
- Modify: `spotify_explorer/app.py` (after `following()`)
- Test: `spotify_explorer/test_app_auth.py`

- [ ] **Step 1: Write the failing test**

Append to `spotify_explorer/test_app_auth.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd spotify_explorer && pytest test_app_auth.py::test_my_playlists_calls_correct_path -v`
Expected: FAIL with `404 Not Found`

- [ ] **Step 3: Add the route**

In `spotify_explorer/app.py`, add after `following()`:

```python
    @app.route("/api/me/playlists")
    def my_playlists():
        return _user_data_route(
            "/me/playlists",
            params={
                "limit": request.args.get("limit", "20"),
                "offset": request.args.get("offset", "0"),
            },
        )
```

- [ ] **Step 4: Run test to verify it passes, then run the full backend suite**

Run: `cd spotify_explorer && pytest -v`
Expected: PASS — all tests (existing + new)

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/app.py spotify_explorer/test_app_auth.py
git commit -m "feat: add /api/me/playlists route"
```

---

## Task 6: Fix 204 handling in the frontend `fetchJSON`

The backend now forwards a real `204` for `/api/me/player` when
nothing is playing. `fetchJSON` today calls `response.json()`
unconditionally, which throws on an empty body and marks the result
`ok: false` — turning "nothing playing" into a fake client error.

No JS test suite exists in this project (established convention —
verified via `npm run build` + manual smoke test instead).

**Files:**
- Modify: `spotify_explorer/frontend/src/composables/useApi.js:3-22`

- [ ] **Step 1: Add the 204 branch to `fetchJSON`**

Replace `fetchJSON` in `spotify_explorer/frontend/src/composables/useApi.js`:

```js
export async function fetchJSON(url, options = {}) {
  let response;
  try {
    response = await fetch(url, options);
  } catch (err) {
    return { ok: false, status: 0, data: null, error: String(err) };
  }

  if (response.status === 204) {
    return { ok: response.ok, status: 204, data: {}, error: null };
  }

  try {
    const data = await response.json();
    return { ok: response.ok, status: response.status, data, error: null };
  } catch (err) {
    return {
      ok: false,
      status: response.status,
      data: null,
      error: `Resposta HTTP ${response.status} não é JSON válido: ${err}`,
    };
  }
}
```

- [ ] **Step 2: Verify the existing frontend still builds**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds (this file is already imported everywhere, so a syntax error would fail the build)

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/composables/useApi.js
git commit -m "fix: treat HTTP 204 as valid empty data in fetchJSON"
```

---

## Task 7: Add 3 new icons to `Icon.vue`

**Files:**
- Modify: `spotify_explorer/frontend/src/components/Icon.vue:7-21`

- [ ] **Step 1: Add the new icon paths**

In `spotify_explorer/frontend/src/components/Icon.vue`, add 3 entries to the `paths` object (after the `"new-releases"` entry, line 20):

```js
  "new-releases": "M10 2l2.163 4.382 4.837.703-3.5 3.412.826 4.815L10 13.033l-4.326 2.279.826-4.815-3.5-3.412 4.837-.703L10 2z",
  player: "M6 4.5v11l9-5.5-9-5.5z",
  following: "M10 10a4 4 0 100-8 4 4 0 000 8zm0 2c-4.4 0-8 2.2-8 5v1a1 1 0 001 1h14a1 1 0 001-1v-1c0-2.8-3.6-5-8-5z",
  folder: "M3 5a2 2 0 012-2h3l2 2h5a2 2 0 012 2v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5z",
```

- [ ] **Step 2: Verify the build still succeeds**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/components/Icon.vue
git commit -m "feat: add player, following, and folder icons"
```

---

## Task 8: Stop click propagation on `MediaItemRow`'s external link

New tabs will wrap `MediaItemRow` in a clickable button (cross-tab
navigation — see Tasks 12-13). Without this fix, clicking the
"Abrir no Spotify" external-link icon inside a row would also
trigger the wrapping button's click handler and navigate away from
the intended external link.

**Files:**
- Modify: `spotify_explorer/frontend/src/components/MediaItemRow.vue:20`

- [ ] **Step 1: Add `.stop` to the link's click handling**

In `spotify_explorer/frontend/src/components/MediaItemRow.vue`, change line 20 from:

```html
    <a v-if="url" :href="url" target="_blank" rel="noopener" class="media-item-link" aria-label="Abrir no Spotify">
```

to:

```html
    <a v-if="url" :href="url" target="_blank" rel="noopener" class="media-item-link" aria-label="Abrir no Spotify" @click.stop>
```

- [ ] **Step 2: Verify the build still succeeds**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds (this component is already used by every existing tab, so this also regression-checks nothing else broke)

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/components/MediaItemRow.vue
git commit -m "fix: stop external-link clicks from bubbling to a wrapping row handler"
```

---

## Task 9: Add clickable-row CSS

**Files:**
- Modify: `spotify_explorer/frontend/src/style.css` (near the "Media item row" block, after line 268)

- [ ] **Step 1: Add the CSS rule**

In `spotify_explorer/frontend/src/style.css`, add after the `.media-item-row:hover` block (after line 268):

```css
.media-item-clickable {
  display: block;
  width: 100%;
  background: none;
  border: none;
  padding: 0;
  text-align: left;
  cursor: pointer;
  font: inherit;
  color: inherit;
}
```

- [ ] **Step 2: Verify the build still succeeds**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/style.css
git commit -m "feat: add clickable-row style for cross-tab navigation"
```

---

## Task 10: Create `useTabNavigation.js` composable

Module-scoped shared state (same pattern as `useAuthStatus.js`) so
any tab can say "switch to tab X with this ID" without prop-drilling
through `App.vue`. `useNavigationTarget` is the consumer half: a tab
that can be navigated *to* calls it once with its own tab id and a
callback; it fires that callback both on first mount (covers being
navigated to before the target tab has ever been opened, since
`KeepAlive`-wrapped tabs don't exist until first rendered) and on
every subsequent change to the shared pending state (covers
navigating to an already-mounted tab again).

**Files:**
- Create: `spotify_explorer/frontend/src/composables/useTabNavigation.js`

- [ ] **Step 1: Write the composable**

```js
import { onMounted, ref, watch } from "vue";

const pending = ref(null); // { tab: string, id: string } | null

export function useTabNavigation() {
  function goTo(tab, id) {
    pending.value = { tab, id };
  }

  function consume(forTab) {
    if (pending.value?.tab !== forTab) return null;
    const id = pending.value.id;
    pending.value = null;
    return id;
  }

  return { pending, goTo, consume };
}

export function useNavigationTarget(tabId, onId) {
  const { pending, consume } = useTabNavigation();

  function applyPending() {
    const id = consume(tabId);
    if (id) onId(id);
  }

  onMounted(applyPending);
  watch(pending, applyPending);
}
```

This file has no isolated build check here — it has no default
export reachable from `App.vue` yet, so a syntax error wouldn't
surface until it's imported. It gets exercised for real in Task 12
(first real usage), which does an isolated build check.

- [ ] **Step 2: Commit**

```bash
git add spotify_explorer/frontend/src/composables/useTabNavigation.js
git commit -m "feat: add useTabNavigation composable for cross-tab navigation"
```

---

## Task 11: Create `PlayerTab.vue`

**Files:**
- Create: `spotify_explorer/frontend/src/tabs/PlayerTab.vue`
- Modify (temporarily): `spotify_explorer/frontend/src/App.vue`

- [ ] **Step 1: Write the component**

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
              <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" />
            </div>
          </div>
        </template>
      </ResultPanel>
    </div>
  </section>
</template>
```

- [ ] **Step 2: Temporarily wire it into `App.vue` to verify it compiles**

In `spotify_explorer/frontend/src/App.vue`, temporarily add the import next to the other tab imports:

```js
import PlayerTab from "./tabs/PlayerTab.vue";
```

and temporarily add an entry to the `tabs` array:

```js
  { id: "player", label: "Player", icon: "player", component: PlayerTab },
```

- [ ] **Step 3: Build and confirm it compiles**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds, module count includes the new file

- [ ] **Step 4: Revert the temporary wiring**

```bash
git checkout -- spotify_explorer/frontend/src/App.vue
```

(`App.vue` gets its real, permanent wiring in Task 16, alongside `FollowingTab` and `MyPlaylistsTab`.)

- [ ] **Step 5: Commit the new file**

```bash
git add spotify_explorer/frontend/src/tabs/PlayerTab.vue
git commit -m "feat: add Player tab (read-only /me/player + queue)"
```

---

## Task 12: Create `FollowingTab.vue`

**Files:**
- Create: `spotify_explorer/frontend/src/tabs/FollowingTab.vue`
- Modify (temporarily): `spotify_explorer/frontend/src/App.vue`

- [ ] **Step 1: Write the component**

```vue
<script setup>
import { computed, reactive, ref } from "vue";
import { useApi } from "../composables/useApi.js";
import { useAuthStatus } from "../composables/useAuthStatus.js";
import { useTabNavigation } from "../composables/useTabNavigation.js";
import { artistSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const { state: authState } = useAuthStatus();
const { goTo } = useTabNavigation();
const limit = ref(20);
const { status, call } = useApi();
const result = reactive({ data: null });

const items = computed(() => {
  const raw = result.data?.artists?.items;
  if (!Array.isArray(raw)) return [];
  return raw
    .map((artist) => {
      const summary = artistSummary(artist);
      return summary ? { id: artist.id, ...summary } : null;
    })
    .filter((item) => item !== null);
});

async function fetchFollowing() {
  const { data } = await call(`/api/me/following?limit=${Number(limit.value)}`);
  result.data = data;
}
</script>

<template>
  <section>
    <h2>Seguindo</h2>
    <div v-if="!authState.loggedIn">
      <p>Nenhum usuário conectado.</p>
      <a class="btn" href="/login">Conectar Spotify</a>
    </div>
    <div v-else>
      <form @submit.prevent="fetchFollowing">
        <label>Limit <input type="number" v-model.number="limit" min="1" max="50"></label>
        <button type="submit" class="btn">Buscar artistas seguidos</button>
      </form>
      <ResultPanel
        :status="status"
        :data="result.data"
        empty-hint="Clique em Buscar pra ver os artistas que você segue"
      >
        <template #preview>
          <button
            v-for="(item, i) in items"
            :key="i"
            type="button"
            class="media-item-clickable"
            @click="goTo('artist', item.id)"
          >
            <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" />
          </button>
        </template>
      </ResultPanel>
    </div>
  </section>
</template>
```

- [ ] **Step 2: Temporarily wire it into `App.vue` to verify it compiles**

Same pattern as Task 11 Step 2 — add:

```js
import FollowingTab from "./tabs/FollowingTab.vue";
```

and:

```js
  { id: "following", label: "Seguindo", icon: "following", component: FollowingTab },
```

- [ ] **Step 3: Build and confirm it compiles**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds

- [ ] **Step 4: Revert the temporary wiring**

```bash
git checkout -- spotify_explorer/frontend/src/App.vue
```

- [ ] **Step 5: Commit the new file**

```bash
git add spotify_explorer/frontend/src/tabs/FollowingTab.vue
git commit -m "feat: add Seguindo tab (/me/following, navigates to Artist tab)"
```

---

## Task 13: Create `MyPlaylistsTab.vue`

**Files:**
- Create: `spotify_explorer/frontend/src/tabs/MyPlaylistsTab.vue`
- Modify (temporarily): `spotify_explorer/frontend/src/App.vue`

- [ ] **Step 1: Write the component**

```vue
<script setup>
import { computed, reactive, ref } from "vue";
import { useApi } from "../composables/useApi.js";
import { useAuthStatus } from "../composables/useAuthStatus.js";
import { useTabNavigation } from "../composables/useTabNavigation.js";
import { playlistSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const { state: authState } = useAuthStatus();
const { goTo } = useTabNavigation();
const limit = ref(20);
const { status, call } = useApi();
const result = reactive({ data: null });

const items = computed(() => {
  const raw = result.data?.items;
  if (!Array.isArray(raw)) return [];
  return raw
    .map((playlist) => {
      const summary = playlistSummary(playlist);
      if (!summary) return null;
      return {
        id: playlist.id,
        ...summary,
        subtitle: `${summary.subtitle} — ${playlist.public ? "pública" : "privada"}`,
      };
    })
    .filter((item) => item !== null);
});

async function fetchPlaylists() {
  const { data } = await call(`/api/me/playlists?limit=${Number(limit.value)}`);
  result.data = data;
}
</script>

<template>
  <section>
    <h2>Minhas Playlists</h2>
    <div v-if="!authState.loggedIn">
      <p>Nenhum usuário conectado.</p>
      <a class="btn" href="/login">Conectar Spotify</a>
    </div>
    <div v-else>
      <form @submit.prevent="fetchPlaylists">
        <label>Limit <input type="number" v-model.number="limit" min="1" max="50"></label>
        <button type="submit" class="btn">Buscar minhas playlists</button>
      </form>
      <ResultPanel
        :status="status"
        :data="result.data"
        empty-hint="Clique em Buscar pra listar suas playlists"
      >
        <template #preview>
          <button
            v-for="(item, i) in items"
            :key="i"
            type="button"
            class="media-item-clickable"
            @click="goTo('playlist', item.id)"
          >
            <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" />
          </button>
        </template>
      </ResultPanel>
    </div>
  </section>
</template>
```

- [ ] **Step 2: Temporarily wire it into `App.vue` to verify it compiles**

Same pattern as Task 11 Step 2 — add:

```js
import MyPlaylistsTab from "./tabs/MyPlaylistsTab.vue";
```

and:

```js
  { id: "my-playlists", label: "Minhas Playlists", icon: "folder", component: MyPlaylistsTab },
```

- [ ] **Step 3: Build and confirm it compiles**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds

- [ ] **Step 4: Revert the temporary wiring**

```bash
git checkout -- spotify_explorer/frontend/src/App.vue
```

- [ ] **Step 5: Commit the new file**

```bash
git add spotify_explorer/frontend/src/tabs/MyPlaylistsTab.vue
git commit -m "feat: add Minhas Playlists tab (/me/playlists, navigates to Playlist tab)"
```

---

## Task 14: Wire navigation consumption into `PlaylistTab.vue`

**Files:**
- Modify: `spotify_explorer/frontend/src/tabs/PlaylistTab.vue`

- [ ] **Step 1: Add the navigation target**

In `spotify_explorer/frontend/src/tabs/PlaylistTab.vue`, add the import (after the existing `useHistory` import, line 4):

```js
import { useNavigationTarget } from "../composables/useTabNavigation.js";
```

Then, after the `onSubmit` function definition (after line 25, before the `</script>` close), add:

```js
useNavigationTarget("playlist", (id) => {
  playlistId.value = id;
  onSubmit();
});
```

The full `<script setup>` block should now read:

```vue
<script setup>
import { computed, reactive, ref } from "vue";
import { useApi } from "../composables/useApi.js";
import { useHistory } from "../composables/useHistory.js";
import { useNavigationTarget } from "../composables/useTabNavigation.js";
import { trackSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import PlaylistPreview from "../components/previews/PlaylistPreview.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const playlistId = ref("");
const { status, call } = useApi();
const result = reactive({ data: null });
const { items: history, add: addToHistory } = useHistory("playlist");

const tracks = computed(() => {
  const items = result.data?.tracks?.items;
  if (!Array.isArray(items)) return [];
  return items.map((item) => trackSummary(item.track)).filter((item) => item !== null);
});

async function onSubmit() {
  const { data } = await call(`/api/playlist/${playlistId.value}`);
  result.data = data;
  addToHistory(playlistId.value);
}

useNavigationTarget("playlist", (id) => {
  playlistId.value = id;
  onSubmit();
});
</script>
```

(Template is unchanged.)

- [ ] **Step 2: Verify the build still succeeds**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/PlaylistTab.vue
git commit -m "feat: make Playlist tab a cross-tab navigation target"
```

---

## Task 15: Wire navigation consumption into `ArtistTab.vue`

**Files:**
- Modify: `spotify_explorer/frontend/src/tabs/ArtistTab.vue`

- [ ] **Step 1: Add the navigation target**

In `spotify_explorer/frontend/src/tabs/ArtistTab.vue`, add the import (after the existing `useHistory` import, line 4):

```js
import { useNavigationTarget } from "../composables/useTabNavigation.js";
```

Then, after the `onSubmit` function definition (after line 50, before the `</script>` close), add:

```js
useNavigationTarget("artist", (id) => {
  artistId.value = id;
  onSubmit();
});
```

The full `<script setup>` block should now read:

```vue
<script setup>
import { computed, reactive, ref } from "vue";
import { fetchJSON } from "../composables/useApi.js";
import { useHistory } from "../composables/useHistory.js";
import { useNavigationTarget } from "../composables/useTabNavigation.js";
import { trackSummary, artistSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import ArtistPreview from "../components/previews/ArtistPreview.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const artistId = ref("");
const status = reactive({ text: "", className: "status", loading: false });
const result = reactive({ data: null });
const { items: history, add: addToHistory } = useHistory("artist");

const topTracksItems = computed(() => {
  if (!result.data?.top_tracks?.tracks) return [];
  return result.data.top_tracks.tracks.map(trackSummary).filter((item) => item !== null);
});

const relatedArtistsItems = computed(() => {
  if (!result.data?.related_artists?.artists) return [];
  return result.data.related_artists.artists.map(artistSummary).filter((item) => item !== null);
});

async function onSubmit() {
  status.loading = true;
  status.text = "Carregando...";
  status.className = "status";

  const [artist, topTracks, albums, relatedArtists] = await Promise.all([
    fetchJSON(`/api/artist/${artistId.value}`),
    fetchJSON(`/api/artist/${artistId.value}/top-tracks`),
    fetchJSON(`/api/artist/${artistId.value}/albums`),
    fetchJSON(`/api/artist/${artistId.value}/related-artists`),
  ]);

  status.loading = false;
  const results = [artist, topTracks, albums, relatedArtists];
  const allOk = results.every((r) => r.ok);
  const statuses = results.map((r) => (r.status === 0 ? "erro de rede" : r.status)).join(", ");
  status.text = `HTTP ${statuses}`;
  status.className = "status " + (allOk ? "status-ok" : "status-error");
  result.data = {
    artist: artist.data,
    top_tracks: topTracks.data,
    albums: albums.data,
    related_artists: relatedArtists.data,
  };
  addToHistory(artistId.value);
}

useNavigationTarget("artist", (id) => {
  artistId.value = id;
  onSubmit();
});
</script>
```

(Template is unchanged.)

- [ ] **Step 2: Verify the build still succeeds**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/ArtistTab.vue
git commit -m "feat: make Artist tab a cross-tab navigation target"
```

---

## Task 16: Permanently wire the 3 new tabs into `App.vue`

**Files:**
- Modify: `spotify_explorer/frontend/src/App.vue`

- [ ] **Step 1: Add the imports and tabs entries, and the pending-navigation watcher**

Replace the full contents of `spotify_explorer/frontend/src/App.vue`:

```vue
<script setup>
import { onMounted, reactive, ref, watch } from "vue";
import { fetchJSON } from "./composables/useApi.js";
import { useAuthStatus } from "./composables/useAuthStatus.js";
import { useTabNavigation } from "./composables/useTabNavigation.js";
import AppSidebar from "./components/AppSidebar.vue";
import SearchTab from "./tabs/SearchTab.vue";
import TrackTab from "./tabs/TrackTab.vue";
import ArtistTab from "./tabs/ArtistTab.vue";
import RecommendationsTab from "./tabs/RecommendationsTab.vue";
import MeusDadosTab from "./tabs/MeusDadosTab.vue";
import AlbumTab from "./tabs/AlbumTab.vue";
import PlaylistTab from "./tabs/PlaylistTab.vue";
import NewReleasesTab from "./tabs/NewReleasesTab.vue";
import PlayerTab from "./tabs/PlayerTab.vue";
import FollowingTab from "./tabs/FollowingTab.vue";
import MyPlaylistsTab from "./tabs/MyPlaylistsTab.vue";

const tabs = [
  { id: "search", label: "Search", icon: "search", component: SearchTab },
  { id: "track", label: "Track & Audio", icon: "disc", component: TrackTab },
  { id: "artist", label: "Artist", icon: "mic", component: ArtistTab },
  { id: "album", label: "Album", icon: "album", component: AlbumTab },
  { id: "playlist", label: "Playlist", icon: "playlist", component: PlaylistTab },
  { id: "new-releases", label: "New Releases", icon: "new-releases", component: NewReleasesTab },
  { id: "recommendations", label: "Recommendations", icon: "sparkles", component: RecommendationsTab },
  { id: "me", label: "Meus dados", icon: "heart", component: MeusDadosTab },
  { id: "player", label: "Player", icon: "player", component: PlayerTab },
  { id: "following", label: "Seguindo", icon: "following", component: FollowingTab },
  { id: "my-playlists", label: "Minhas Playlists", icon: "folder", component: MyPlaylistsTab },
];

const activeTab = ref("search");
const config = reactive({ missingCredentials: false });
const authError = ref(new URLSearchParams(window.location.search).get("auth_error"));
const { state: authState, refresh: refreshAuthStatus } = useAuthStatus();
const { pending } = useTabNavigation();

watch(pending, (nav) => {
  if (nav) activeTab.value = nav.tab;
});

onMounted(async () => {
  const result = await fetchJSON("/api/config");
  if (result.ok) {
    config.missingCredentials = Boolean(result.data.missing_credentials);
  }
  refreshAuthStatus();
});
</script>

<template>
  <div class="app-shell">
    <AppSidebar :tabs="tabs" :active-tab="activeTab" :auth-state="authState" @select="activeTab = $event" />

    <main class="app-main">
      <div v-if="config.missingCredentials" class="banner banner-error">
        SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET não configurados. Copie
        <code>.env.example</code> para <code>.env</code> e preencha com um app criado no
        <a href="https://developer.spotify.com/dashboard" target="_blank" rel="noopener">Spotify Developer Dashboard</a>.
      </div>

      <div v-if="authError" class="banner banner-error">Erro no login: {{ authError }}</div>

      <KeepAlive>
        <component :is="tabs.find((t) => t.id === activeTab).component" />
      </KeepAlive>
    </main>
  </div>
</template>
```

- [ ] **Step 2: Build and confirm everything compiles together**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds, module count includes all 3 new tabs + the composable

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/App.vue
git commit -m "feat: wire Player, Seguindo, and Minhas Playlists tabs into the sidebar"
```

---

## Task 17: Update `spotify_explorer/README.md`

**Files:**
- Modify: `spotify_explorer/README.md`

- [ ] **Step 1: Document the re-login requirement, the 3 new tabs, and extend the smoke-test checklist**

In `spotify_explorer/README.md`, insert a callout paragraph right after the numbered setup list ends (after "7. Abra `http://127.0.0.1:5000`", before the "## Rodando os testes" heading). Do not renumber the existing list:

```markdown
> **Se você já tinha uma sessão logada de antes da Fase 2:** os escopos
> do OAuth mudaram (`user-read-playback-state`,
> `user-read-currently-playing`, `user-follow-read`,
> `playlist-read-private` foram adicionados). Deslogue e logue de novo
> — a Spotify só pede consentimento dos escopos novos numa nova
> autorização; um token antigo não os tem.
```

In the "O que cada aba faz" section, add after the "Meus dados" bullet:

```markdown
- **Player** — `GET /me/player` (o que tá tocando, dispositivo,
  progresso) + `GET /me/player/queue` (fila) — só leitura, sem
  controles de reprodução. Requer login.
- **Seguindo** — `GET /me/following?type=artist` (artistas seguidos).
  Clicar num artista abre os detalhes na aba Artist. Requer login.
- **Minhas Playlists** — `GET /me/playlists` (inclui privadas do
  usuário logado). Clicar numa playlist abre os detalhes na aba
  Playlist. Requer login.
```

In the "Restrições conhecidas da API" section, add:

```markdown
`/me/player` e `/me/player/queue` devolvem 204 (sem corpo) quando não
há reprodução ativa — a ferramenta mostra isso como "Nada tocando no
momento", não como erro.
```

In the "Checklist de smoke test manual" section, add:

```markdown
- [ ] Player mostra "Nada tocando" quando não há reprodução ativa, e
      o estado real (faixa/dispositivo/fila) quando há
- [ ] Seguindo lista os artistas seguidos; clicar num item abre a aba
      Artist com os detalhes
- [ ] Minhas Playlists lista as playlists (inclusive privadas);
      clicar num item abre a aba Playlist com os detalhes
```

- [ ] **Step 2: Commit**

```bash
git add spotify_explorer/README.md
git commit -m "docs: document Player, Seguindo, and Minhas Playlists tabs"
```

---

## Task 18: Final verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full backend test suite**

Run: `cd spotify_explorer && pytest -v`
Expected: PASS — every test, old and new

- [ ] **Step 2: Run the full frontend build**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds with no errors

- [ ] **Step 3: Confirm `App.vue` has no leftover temporary wiring**

Run: `git diff main -- spotify_explorer/frontend/src/App.vue`
Expected: the diff shows exactly the 3 new imports, 3 new tabs-array entries, the `useTabNavigation` import/usage, and the `watch` import — nothing else. (Cross-checks that every "temporarily wire, build, revert" step in Tasks 11-13 actually reverted cleanly.)

- [ ] **Step 4: Manual smoke test**

Start the backend (`cd spotify_explorer && python app.py`) and frontend dev server (`cd spotify_explorer/frontend && npm run dev`), open `http://127.0.0.1:5173`, log out and log back in (to pick up the new scopes), then walk the 3 new checklist items added to `spotify_explorer/README.md` in Task 17.
