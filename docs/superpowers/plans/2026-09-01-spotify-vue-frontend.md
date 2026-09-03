# Spotify Explorer Vue Frontend Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `spotify_explorer`'s vanilla-JS frontend (`templates/index.html` + `static/app.js` + `static/style.css`) with a Vue 3 + Vite single-page app, with full feature parity (same 5 tabs, same fields, same error-handling semantics) and only 3 small, backward-compatible integration touches to the Flask backend.

**Architecture:** A new `spotify_explorer/frontend/` Vite project (Vue 3, no Pinia/vue-router — a single shared reactive composable covers the one bit of cross-component state). Two composables (`useApi.js`, `useAuthStatus.js`) replace `app.js`'s `fetchJSON`/`callEndpoint`/`loadUserStatus`. One recursive `JsonViewer.vue` component replaces `renderValue`/`renderContainer`. `App.vue` replaces the tab-switching + banners; a `.vue` file per tab replaces each `init*Form` function. The Flask backend gains a `GET /api/config` route (replaces the old Jinja `missing_credentials` conditional), an `index()` that serves the Vite build output (with a graceful "not built yet" fallback), and a `FRONTEND_URL` config value so `/callback`/`/logout` redirect correctly whether the app is running via `npm run build` (Flask serves everything on :5000) or `npm run dev` (Vite on :5173, proxying back to Flask).

**Tech Stack:** Vue 3 (Composition API, `<script setup>`), Vite 5, no additional JS libraries (no Pinia, no vue-router, no Vitest — see spec for rationale). Backend: unchanged Flask/pytest.

**Spec:** `docs/superpowers/specs/2026-09-01-spotify-vue-frontend-design.md`

---

## Task 1: Backend integration — `FRONTEND_URL`, `/api/config`, build-serving `index()`

**Files:**
- Modify: `spotify_explorer/app.py`
- Modify: `spotify_explorer/test_app.py`
- Modify: `spotify_explorer/test_app_auth.py`
- Modify: `spotify_explorer/.env.example`

- [ ] **Step 1: Add the failing tests**

Append to `spotify_explorer/test_app.py`:

```python
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
```

Append to `spotify_explorer/test_app_auth.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify the new ones fail, existing ones still pass**

Run: `cd spotify_explorer && pytest test_app.py test_app_auth.py -v`
Expected: the 6 new tests FAIL (`test_index_shows_build_instructions_when_frontend_not_built` and `test_index_serves_built_frontend_when_present` fail because the route still renders the Jinja template and ignores `FRONTEND_DIST_DIR`; the 2 `/api/config` tests fail with 404; the 2 `FRONTEND_URL` tests fail because redirects still go to `/`). All pre-existing tests still PASS unchanged.

- [ ] **Step 3: Update `app.py`**

Change the import line near the top of `spotify_explorer/app.py` from:
```python
from flask import Flask, jsonify, redirect, render_template, request, url_for
```
to:
```python
from urllib.parse import urlencode

from flask import Flask, jsonify, redirect, request, send_from_directory
```
(`render_template` and `url_for` become unused once `index()`/`callback()`/`logout()` are updated below — remove them. `urlencode` is new, needed to build the `auth_error` query string manually now that we're not using `url_for`.)

In `create_app()`, add two lines right after the existing `SPOTIFY_REDIRECT_URI` config line:
```python
    app.config["FRONTEND_URL"] = os.environ.get("FRONTEND_URL", "/")
    app.config["FRONTEND_DIST_DIR"] = os.path.join(app.static_folder, "frontend")
```

Replace the `index()` route entirely:
```python
    @app.route("/")
    def index():
        index_path = os.path.join(app.config["FRONTEND_DIST_DIR"], "index.html")
        if not os.path.exists(index_path):
            return (
                "<h1>Frontend não buildado</h1>"
                "<p>Rode <code>cd spotify_explorer/frontend && npm install && npm run build</code> "
                "e recarregue esta página.</p>"
            ), 200
        return send_from_directory(app.config["FRONTEND_DIST_DIR"], "index.html")
```

Add a new route immediately after `index()`:
```python
    @app.route("/api/config")
    def api_config():
        missing_credentials = not (
            app.config["SPOTIFY_CLIENT_ID"] and app.config["SPOTIFY_CLIENT_SECRET"]
        )
        return jsonify({"missing_credentials": missing_credentials})
```

Replace the `callback()` route's error handling and final redirect (leave the `try`/`exchange_code(...)` call itself untouched):
```python
    @app.route("/callback")
    def callback():
        error = request.args.get("error")
        if error:
            return redirect(f"{app.config['FRONTEND_URL']}?{urlencode({'auth_error': error})}")

        try:
            user_auth.exchange_code(
                request.args.get("code"),
                request.args.get("state"),
                app.config["SPOTIFY_CLIENT_ID"],
                app.config["SPOTIFY_CLIENT_SECRET"],
                app.config["SPOTIFY_REDIRECT_URI"],
            )
        except ValueError as exc:
            return redirect(f"{app.config['FRONTEND_URL']}?{urlencode({'auth_error': str(exc)})}")

        return redirect(app.config["FRONTEND_URL"])
```

Replace the `logout()` route:
```python
    @app.route("/logout")
    def logout():
        user_auth.logout()
        return redirect(app.config["FRONTEND_URL"])
```

Everything else in `app.py` (all `/api/*` routes, `_user_data_route`, `login()`, `me()`, the `if __name__ == "__main__":` block) stays exactly as it is.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd spotify_explorer && pytest test_app.py test_app_auth.py -v`
Expected: all pass (15 in `test_app.py`: 11 prior + 4 new; 15 in `test_app_auth.py`: 13 prior + 2 new)

Run: `cd spotify_explorer && pytest -v`
Expected: all 55 tests pass (current total is 49; this task's 6 new tests bring it to 55)

- [ ] **Step 5: Add `FRONTEND_URL` to `.env.example`**

Add this line to the end of `spotify_explorer/.env.example`:
```
FRONTEND_URL=
```

- [ ] **Step 6: Commit**

```bash
git add spotify_explorer/app.py spotify_explorer/test_app.py spotify_explorer/test_app_auth.py spotify_explorer/.env.example
git commit -m "feat: add /api/config, FRONTEND_URL-aware redirects, and build-serving index route"
```

---

## Task 2: Vite scaffold, frontend shell, and the 4 catalog tabs

**Files:**
- Create: `spotify_explorer/frontend/package.json`
- Create: `spotify_explorer/frontend/vite.config.js`
- Create: `spotify_explorer/frontend/index.html`
- Create: `spotify_explorer/frontend/src/main.js`
- Create: `spotify_explorer/frontend/src/style.css`
- Create: `spotify_explorer/frontend/src/composables/useApi.js`
- Create: `spotify_explorer/frontend/src/components/JsonViewer.vue`
- Create: `spotify_explorer/frontend/src/tabs/SearchTab.vue`
- Create: `spotify_explorer/frontend/src/tabs/TrackTab.vue`
- Create: `spotify_explorer/frontend/src/tabs/ArtistTab.vue`
- Create: `spotify_explorer/frontend/src/tabs/RecommendationsTab.vue`
- Create: `spotify_explorer/frontend/src/tabs/MeusDadosTab.vue` (stub — replaced in Task 3)
- Create: `spotify_explorer/frontend/src/App.vue`
- Modify: `.gitignore` (repo root)

No backend logic in this task. No JS test framework exists (deliberate project convention, see spec) — verification is `npm install` + `npm run build` succeeding (Vite's Vue compiler catches template/syntax errors), plus a manual check that Flask serves the built output.

- [ ] **Step 1: Create `package.json`**

```json
{
  "name": "spotify-explorer-frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build"
  },
  "dependencies": {
    "vue": "^3.4.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.1.0",
    "vite": "^5.4.0"
  }
}
```

- [ ] **Step 2: Create `vite.config.js`**

```javascript
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  base: "/static/frontend/",
  build: {
    outDir: "../static/frontend",
    emptyOutDir: true,
  },
  server: {
    proxy: {
      "/api": "http://127.0.0.1:5000",
      "/login": "http://127.0.0.1:5000",
      "/logout": "http://127.0.0.1:5000",
      "/callback": "http://127.0.0.1:5000",
    },
  },
});
```

- [ ] **Step 3: Create the Vite entry HTML**

```html
<!-- spotify_explorer/frontend/index.html -->
<!doctype html>
<html lang="pt-br">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Spotify API Explorer</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
```

- [ ] **Step 4: Create `src/main.js`**

```javascript
import { createApp } from "vue";
import App from "./App.vue";
import "./style.css";

createApp(App).mount("#app");
```

- [ ] **Step 5: Create `src/style.css`**

Migrated from `spotify_explorer/static/style.css`, with the `.tab-panel`/`.tab-panel.active` show/hide rules dropped — they're dead weight under the new architecture, where each tab is its own component and only one is ever mounted at a time (via `<KeepAlive><component :is="..."/></KeepAlive>` in `App.vue`, see Step 13), so there's nothing to show/hide via CSS anymore. Every other rule is unchanged.

```css
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

- [ ] **Step 6: Create `src/composables/useApi.js`**

This is the Vue equivalent of `app.js`'s `fetchJSON`/`callEndpoint` pair — same split, same semantics (network failure vs. non-JSON body vs. real HTTP status are always distinguished, never conflated):

```javascript
import { reactive } from "vue";

export async function fetchJSON(url, options = {}) {
  let response;
  try {
    response = await fetch(url, options);
  } catch (err) {
    return { ok: false, status: 0, data: null, error: String(err) };
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

export function useApi() {
  const status = reactive({ text: "", className: "status" });

  async function call(url, options = {}) {
    status.text = "Carregando...";
    status.className = "status";

    const result = await fetchJSON(url, options);

    if (result.status === 0) {
      status.text = "Erro de rede";
    } else if (result.error) {
      status.text = result.error;
    } else {
      status.text = `HTTP ${result.status}`;
    }
    status.className = "status " + (result.ok ? "status-ok" : "status-error");

    return result;
  }

  return { status, call };
}
```

`fetchJSON` is the pure, side-effect-free primitive (used directly by tabs that make several parallel calls and need to combine them into one status — Track & Audio, Artist). `useApi()` wraps it with a reactive `status` object for tabs that make one call per action and bind that status straight to a status pill (Search, Recommendations, and each action in Meus dados). Note `fetchJSON` never rejects — a network failure is caught internally and returned as a normal `{status: 0, ...}` result — so callers using `Promise.all([fetchJSON(...), ...])` never need a wrapping `try/catch` the way `app.js`'s `initTrackForm`/`initArtistForm` did; that need was fully absorbed into `fetchJSON` itself here.

- [ ] **Step 7: Create `src/components/JsonViewer.vue`**

Recursive collapsible JSON renderer, replacing `renderValue`/`renderContainer`. Vue 3 SFCs using `<script setup>` can reference themselves by their filename automatically (`JsonViewer` here) for recursion — no manual registration needed. All output goes through `{{ }}` text interpolation (Vue auto-escapes), never `v-html`, matching the no-XSS-risk property of the original renderer (this will render live, attacker-influenceable data from Spotify search results):

```vue
<script setup>
defineProps({
  data: {
    type: null,
    default: null,
  },
});

function isContainer(value) {
  return value !== null && typeof value === "object";
}

function entries(value) {
  if (Array.isArray(value)) {
    return value.map((v, i) => [i, v]);
  }
  return Object.entries(value);
}

function brackets(value) {
  return Array.isArray(value) ? ["[", "]"] : ["{", "}"];
}
</script>

<template>
  <template v-if="data === null || data === undefined">
    <span>null</span>
  </template>
  <template v-else-if="isContainer(data)">
    <span v-if="entries(data).length === 0">{{ brackets(data)[0] }}{{ brackets(data)[1] }}</span>
    <details v-else open>
      <summary>{{ brackets(data)[0] }} {{ entries(data).length }} item(s) {{ brackets(data)[1] }}</summary>
      <div class="json-indent">
        <div v-for="[key, val] in entries(data)" :key="key">
          <span class="json-key">{{ key }}: </span>
          <JsonViewer :data="val" />
        </div>
      </div>
    </details>
  </template>
  <template v-else>
    <span>{{ JSON.stringify(data) }}</span>
  </template>
</template>
```

- [ ] **Step 8: Create `src/tabs/SearchTab.vue`**

```vue
<script setup>
import { reactive } from "vue";
import { useApi } from "../composables/useApi.js";
import JsonViewer from "../components/JsonViewer.vue";

const form = reactive({ q: "", type: "track", limit: 10 });
const { status, call } = useApi();
const result = reactive({ data: null });

async function onSubmit() {
  const { data } = await call("/api/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ q: form.q, type: form.type, limit: Number(form.limit) }),
  });
  result.data = data;
}
</script>

<template>
  <section>
    <form @submit.prevent="onSubmit">
      <label>Query <input type="text" v-model="form.q" required></label>
      <label>Type
        <select v-model="form.type">
          <option value="track">track</option>
          <option value="artist">artist</option>
          <option value="album">album</option>
        </select>
      </label>
      <label>Limit <input type="number" v-model.number="form.limit" min="1" max="50"></label>
      <button type="submit">Buscar</button>
    </form>
    <p :class="status.className">{{ status.text }}</p>
    <div class="result"><JsonViewer v-if="result.data !== null" :data="result.data" /></div>
  </section>
</template>
```

- [ ] **Step 9: Create `src/tabs/TrackTab.vue`**

```vue
<script setup>
import { reactive, ref } from "vue";
import { fetchJSON } from "../composables/useApi.js";
import JsonViewer from "../components/JsonViewer.vue";

const trackId = ref("");
const status = reactive({ text: "", className: "status" });
const result = reactive({ data: null });

async function onSubmit() {
  status.text = "Carregando...";
  status.className = "status";

  const [track, audioFeatures, audioAnalysis] = await Promise.all([
    fetchJSON(`/api/track/${trackId.value}`),
    fetchJSON(`/api/audio-features/${trackId.value}`),
    fetchJSON(`/api/audio-analysis/${trackId.value}`),
  ]);

  const results = [track, audioFeatures, audioAnalysis];
  const allOk = results.every((r) => r.ok);
  const statuses = results.map((r) => r.status).join(", ");
  status.text = `HTTP ${statuses}`;
  status.className = "status " + (allOk ? "status-ok" : "status-error");
  result.data = {
    track: track.data,
    audio_features: audioFeatures.data,
    audio_analysis: audioAnalysis.data,
  };
}
</script>

<template>
  <section>
    <form @submit.prevent="onSubmit">
      <label>Track ID <input type="text" v-model="trackId" required placeholder="ex: 11dFghVXANMlKmJXsNCbNl"></label>
      <button type="submit">Buscar track + audio-features + audio-analysis</button>
    </form>
    <p :class="status.className">{{ status.text }}</p>
    <div class="result"><JsonViewer v-if="result.data !== null" :data="result.data" /></div>
  </section>
</template>
```

- [ ] **Step 10: Create `src/tabs/ArtistTab.vue`**

```vue
<script setup>
import { reactive, ref } from "vue";
import { fetchJSON } from "../composables/useApi.js";
import JsonViewer from "../components/JsonViewer.vue";

const artistId = ref("");
const status = reactive({ text: "", className: "status" });
const result = reactive({ data: null });

async function onSubmit() {
  status.text = "Carregando...";
  status.className = "status";

  const [artist, topTracks, albums, relatedArtists] = await Promise.all([
    fetchJSON(`/api/artist/${artistId.value}`),
    fetchJSON(`/api/artist/${artistId.value}/top-tracks`),
    fetchJSON(`/api/artist/${artistId.value}/albums`),
    fetchJSON(`/api/artist/${artistId.value}/related-artists`),
  ]);

  const results = [artist, topTracks, albums, relatedArtists];
  const allOk = results.every((r) => r.ok);
  const statuses = results.map((r) => r.status).join(", ");
  status.text = `HTTP ${statuses}`;
  status.className = "status " + (allOk ? "status-ok" : "status-error");
  result.data = {
    artist: artist.data,
    top_tracks: topTracks.data,
    albums: albums.data,
    related_artists: relatedArtists.data,
  };
}
</script>

<template>
  <section>
    <form @submit.prevent="onSubmit">
      <label>Artist ID <input type="text" v-model="artistId" required placeholder="ex: 0TnOYISbd1XYRBk9myaseg"></label>
      <button type="submit">Buscar artist + top-tracks + albums + related-artists</button>
    </form>
    <p :class="status.className">{{ status.text }}</p>
    <div class="result"><JsonViewer v-if="result.data !== null" :data="result.data" /></div>
  </section>
</template>
```

- [ ] **Step 11: Create `src/tabs/RecommendationsTab.vue`**

```vue
<script setup>
import { reactive } from "vue";
import { useApi } from "../composables/useApi.js";
import JsonViewer from "../components/JsonViewer.vue";

const form = reactive({
  seed_genres: "",
  seed_tracks: "",
  seed_artists: "",
  target_energy: "",
  target_valence: "",
});
const { status, call } = useApi();
const result = reactive({ data: null });

async function onSubmit() {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(form)) {
    if (value) params.set(key, value);
  }
  const { data } = await call(`/api/recommendations?${params}`);
  result.data = data;
}
</script>

<template>
  <section>
    <form @submit.prevent="onSubmit">
      <label>Seed genres (csv) <input type="text" v-model="form.seed_genres" placeholder="pop,rock"></label>
      <label>Seed tracks (csv) <input type="text" v-model="form.seed_tracks"></label>
      <label>Seed artists (csv) <input type="text" v-model="form.seed_artists"></label>
      <label>Target energy (0-1) <input type="number" v-model="form.target_energy" step="0.1" min="0" max="1"></label>
      <label>Target valence (0-1) <input type="number" v-model="form.target_valence" step="0.1" min="0" max="1"></label>
      <button type="submit">Buscar recomendações</button>
    </form>
    <p :class="status.className">{{ status.text }}</p>
    <div class="result"><JsonViewer v-if="result.data !== null" :data="result.data" /></div>
  </section>
</template>
```

- [ ] **Step 12: Create the `MeusDadosTab.vue` stub**

Task 3 replaces this wholesale with the real implementation — it can't be built yet because it depends on `useAuthStatus.js`, which doesn't exist until Task 3. A minimal placeholder unblocks `App.vue` (Step 13), which needs to import all 5 tabs to mount them:

```vue
<template>
  <section>
    <p>Carregando...</p>
  </section>
</template>
```

- [ ] **Step 13: Create `src/App.vue`**

Tab switching, the missing-credentials banner (via the new `/api/config` route), and the `auth_error` banner (read from the URL query string client-side, replacing the old Jinja `{% if auth_error %}`). The logged-in header (`#user-status`) stays empty for now — wired up in Task 3 alongside `MeusDadosTab.vue`. `<KeepAlive>` around the dynamic tab component preserves each tab's form/result state when switching away and back — without it, Vue would unmount and discard a tab's state on every switch, which the old vanilla version never did (it just hid panels with CSS, keeping all state alive in the DOM at all times):

```vue
<script setup>
import { onMounted, reactive, ref } from "vue";
import { fetchJSON } from "./composables/useApi.js";
import SearchTab from "./tabs/SearchTab.vue";
import TrackTab from "./tabs/TrackTab.vue";
import ArtistTab from "./tabs/ArtistTab.vue";
import RecommendationsTab from "./tabs/RecommendationsTab.vue";
import MeusDadosTab from "./tabs/MeusDadosTab.vue";

const tabs = [
  { id: "search", label: "Search", component: SearchTab },
  { id: "track", label: "Track & Audio", component: TrackTab },
  { id: "artist", label: "Artist", component: ArtistTab },
  { id: "recommendations", label: "Recommendations", component: RecommendationsTab },
  { id: "me", label: "Meus dados", component: MeusDadosTab },
];

const activeTab = ref("search");
const config = reactive({ missingCredentials: false });
const authError = ref(new URLSearchParams(window.location.search).get("auth_error"));

onMounted(async () => {
  const result = await fetchJSON("/api/config");
  if (result.ok) {
    config.missingCredentials = Boolean(result.data.missing_credentials);
  }
});
</script>

<template>
  <header>
    <h1>Spotify API Explorer</h1>
    <div id="user-status"></div>
  </header>

  <div v-if="config.missingCredentials" class="banner banner-error">
    SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET não configurados. Copie
    <code>.env.example</code> para <code>.env</code> e preencha com um app criado no
    <a href="https://developer.spotify.com/dashboard" target="_blank" rel="noopener">Spotify Developer Dashboard</a>.
  </div>

  <div v-if="authError" class="banner banner-error">Erro no login: {{ authError }}</div>

  <nav class="tabs">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      class="tab-button"
      :class="{ active: activeTab === tab.id }"
      @click="activeTab = tab.id"
    >
      {{ tab.label }}
    </button>
  </nav>

  <KeepAlive>
    <component :is="tabs.find((t) => t.id === activeTab).component" />
  </KeepAlive>
</template>
```

- [ ] **Step 14: Update the root `.gitignore`**

Add these two lines to the end of the repo-root `.gitignore`:
```
spotify_explorer/frontend/node_modules/
spotify_explorer/static/frontend/
```

- [ ] **Step 15: Install dependencies and build**

Run: `cd spotify_explorer/frontend && npm install`
Expected: installs cleanly, generates `package-lock.json`.

Run: `npm run build`
Expected: builds without errors, produces `spotify_explorer/static/frontend/index.html` and an `assets/` directory alongside it.

- [ ] **Step 16: Verify the backend serves the build**

Run: `cd spotify_explorer && pytest -v`
Expected: all 55 tests still pass (this task added no backend code, just a real build directory Task 1's tests can now also exercise incidentally).

Run: `cd spotify_explorer && python app.py` (in the background or a separate terminal), then in another shell:
```bash
curl -s http://127.0.0.1:5000/ | grep -o '<title>[^<]*</title>'
curl -s http://127.0.0.1:5000/api/config
```
Expected: the title tag shows `Spotify API Explorer` (confirming the Vite build is served, not the old Jinja template or the "not built" fallback), and `/api/config` returns `{"missing_credentials":false}` (or `true`, depending on whether real credentials are in `.env`). Stop the server afterward.

- [ ] **Step 17: Commit**

```bash
git add spotify_explorer/frontend .gitignore
git commit -m "feat: scaffold Vue/Vite frontend with shell and 4 catalog tabs"
```

---

## Task 3: Wire the "Meus dados" tab

**Files:**
- Create: `spotify_explorer/frontend/src/composables/useAuthStatus.js`
- Modify: `spotify_explorer/frontend/src/tabs/MeusDadosTab.vue`
- Modify: `spotify_explorer/frontend/src/App.vue`

- [ ] **Step 1: Create `src/composables/useAuthStatus.js`**

A module-level `reactive()` object shared by every component that calls `useAuthStatus()` — this is the one piece of cross-component state in the app, and a plain shared `reactive` is enough for it (no Pinia needed, see spec):

```javascript
import { reactive } from "vue";
import { fetchJSON } from "./useApi.js";

const state = reactive({ loggedIn: false, profile: null });

async function refresh() {
  const result = await fetchJSON("/api/me");

  if (!result.ok) {
    state.loggedIn = false;
    state.profile = null;
    return;
  }

  state.loggedIn = true;
  state.profile = result.data;
}

export function useAuthStatus() {
  return { state, refresh };
}
```

This mirrors `app.js`'s `loadUserStatus()` exactly: a failed fetch, a non-2xx response, or a non-JSON body all fall through to the same "not logged in" outcome (`fetchJSON` already collapses all three into `{ok: false, ...}` — no separate try/catch needed here, same simplification as `fetchJSON`'s callers elsewhere).

- [ ] **Step 2: Replace `src/tabs/MeusDadosTab.vue`**

Three independent `useApi()` instances (top tracks/artists, saved tracks, recently played) so each action has its own status pill, matching the 3 separate status elements in the original vanilla markup. The two "Top tracks"/"Top artists" buttons are plain `type="button"` handlers passing their target explicitly, instead of the original's `event.submitter.dataset.target` trick — same observable behavior (one shared `time_range` select, two buttons), simpler implementation:

```vue
<script setup>
import { reactive } from "vue";
import { useApi } from "../composables/useApi.js";
import { useAuthStatus } from "../composables/useAuthStatus.js";
import JsonViewer from "../components/JsonViewer.vue";

const { state: authState } = useAuthStatus();

const timeRange = reactive({ value: "medium_term" });

const top = useApi();
const topResult = reactive({ data: null });

const saved = useApi();
const savedResult = reactive({ data: null });

const recentlyPlayed = useApi();
const recentlyPlayedResult = reactive({ data: null });

async function fetchTop(target) {
  const path = target === "artists" ? "/api/me/top/artists" : "/api/me/top/tracks";
  const { data } = await top.call(`${path}?time_range=${timeRange.value}`);
  topResult.data = data;
}

async function fetchSaved() {
  const { data } = await saved.call("/api/me/tracks");
  savedResult.data = data;
}

async function fetchRecentlyPlayed() {
  const { data } = await recentlyPlayed.call("/api/me/player/recently-played?limit=50");
  recentlyPlayedResult.data = data;
}
</script>

<template>
  <section>
    <div v-if="!authState.loggedIn">
      <p>Nenhum usuário conectado.</p>
      <a class="button" href="/login">Conectar Spotify</a>
    </div>
    <div v-else>
      <p>Logado como: {{ authState.profile.display_name || authState.profile.id }}</p>
      <a class="button" href="/logout">Desconectar</a>

      <fieldset>
        <legend>Top tracks / artists</legend>
        <form @submit.prevent>
          <label>Time range
            <select v-model="timeRange.value">
              <option value="short_term">short_term (~4 semanas)</option>
              <option value="medium_term">medium_term (~6 meses)</option>
              <option value="long_term">long_term (vários anos)</option>
            </select>
          </label>
          <button type="button" @click="fetchTop('tracks')">Top tracks</button>
          <button type="button" @click="fetchTop('artists')">Top artists</button>
        </form>
        <p :class="top.status.className">{{ top.status.text }}</p>
        <div class="result"><JsonViewer v-if="topResult.data !== null" :data="topResult.data" /></div>
      </fieldset>

      <fieldset>
        <legend>Faixas curtidas</legend>
        <button type="button" @click="fetchSaved">Buscar curtidas</button>
        <p :class="saved.status.className">{{ saved.status.text }}</p>
        <div class="result"><JsonViewer v-if="savedResult.data !== null" :data="savedResult.data" /></div>
      </fieldset>

      <fieldset>
        <legend>Tocadas recentemente</legend>
        <button type="button" @click="fetchRecentlyPlayed">Buscar recentes (máx. 50)</button>
        <p :class="recentlyPlayed.status.className">{{ recentlyPlayed.status.text }}</p>
        <div class="result"><JsonViewer v-if="recentlyPlayedResult.data !== null" :data="recentlyPlayedResult.data" /></div>
      </fieldset>
    </div>
  </section>
</template>
```

- [ ] **Step 3: Wire `useAuthStatus` into `App.vue`**

In `spotify_explorer/frontend/src/App.vue`:

Add this import alongside the existing ones:
```javascript
import { useAuthStatus } from "./composables/useAuthStatus.js";
```

Add this line inside `<script setup>`, after the `const authError = ...` line:
```javascript
const { state: authState, refresh: refreshAuthStatus } = useAuthStatus();
```

Change the `onMounted` block from:
```javascript
onMounted(async () => {
  const result = await fetchJSON("/api/config");
  if (result.ok) {
    config.missingCredentials = Boolean(result.data.missing_credentials);
  }
});
```
to:
```javascript
onMounted(async () => {
  const result = await fetchJSON("/api/config");
  if (result.ok) {
    config.missingCredentials = Boolean(result.data.missing_credentials);
  }
  refreshAuthStatus();
});
```

Change the header line from:
```html
    <div id="user-status"></div>
```
to:
```html
    <div id="user-status">{{ authState.loggedIn ? (authState.profile.display_name || authState.profile.id) : "" }}</div>
```

Nothing else in `App.vue` changes.

- [ ] **Step 4: Build and verify**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: builds without errors.

Run: `cd spotify_explorer && pytest -v`
Expected: all 55 tests still pass (this task touches no backend code).

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/frontend/src/composables/useAuthStatus.js spotify_explorer/frontend/src/tabs/MeusDadosTab.vue spotify_explorer/frontend/src/App.vue
git commit -m "feat: wire Meus dados tab (login status, top tracks/artists, saved tracks, recently played)"
```

---

## Task 4: Remove the old vanilla frontend

**Files:**
- Delete: `spotify_explorer/templates/index.html`
- Delete: `spotify_explorer/static/app.js`
- Delete: `spotify_explorer/static/style.css`

Both `render_template` and the old `templates/index.html` are already unused as of Task 1 (the `index()` route no longer calls `render_template`); `static/app.js`/`static/style.css` are superseded by the Vue app built in Tasks 2-3. Nothing in the backend or its tests references these files.

- [ ] **Step 1: Delete the files**

```bash
git rm spotify_explorer/templates/index.html spotify_explorer/static/app.js spotify_explorer/static/style.css
```

(`git rm` removes the empty `spotify_explorer/templates/` directory implicitly, since git doesn't track empty directories.)

- [ ] **Step 2: Verify nothing else references them**

Run: `grep -rn "render_template\|templates/index.html\|static/app.js\|static/style.css" spotify_explorer/app.py spotify_explorer/test_app.py spotify_explorer/test_app_auth.py`
Expected: no output (no remaining references).

Run: `cd spotify_explorer && pytest -v`
Expected: all 55 tests still pass.

- [ ] **Step 3: Commit**

```bash
git commit -m "chore: remove old vanilla-JS frontend, superseded by Vue"
```

---

## Task 5: Update `README.md` for the Vue/Vite setup

**Files:**
- Modify: `spotify_explorer/README.md`

- [ ] **Step 1: Rewrite the Setup and add a Frontend development section**

Replace steps 4-6 of the "## Setup" section (which currently say `pip install ...` then `python app.py` then "abra http://127.0.0.1:5000") with:

```markdown
4. Instale as dependências do backend:
   ```
   pip install -r requirements.txt -r spotify_explorer/requirements.txt
   ```
5. Instale as dependências do frontend e gere o build:
   ```
   cd spotify_explorer/frontend
   npm install
   npm run build
   cd ..
   ```
6. Rode o backend (que já serve o frontend buildado):
   ```
   python app.py
   ```
7. Abra `http://127.0.0.1:5000`
```

Add a new section right after "## Rodando os testes":

```markdown
## Desenvolvendo o frontend (hot-reload)

Pra mexer nos componentes Vue com hot-reload, em vez do passo 5-6 acima,
rode dois processos em paralelo:

```
# terminal 1 — backend
python app.py

# terminal 2 — frontend com hot-reload
cd spotify_explorer/frontend
npm run dev
```

Abra `http://127.0.0.1:5173` (não a `:5000`) — o Vite serve o frontend
com hot-reload e proxeia `/api`, `/login`, `/logout`, `/callback` pro
Flask automaticamente. Pra isso funcionar com o login (OAuth), adicione
`FRONTEND_URL=http://127.0.0.1:5173` no `.env` — sem isso, depois do
login a Spotify te devolve pra `:5000` (o Flask), não pro Vite.
```

- [ ] **Step 2: Sanity-check paths**

Confirm every path/command mentioned exists or is correct: `spotify_explorer/frontend/package.json` (Task 2), `FRONTEND_URL` in `.env.example` (Task 1), port 5173 (Vite's default, unchanged in `vite.config.js`).

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/README.md
git commit -m "docs: update README for the Vue/Vite frontend setup and dev workflow"
```

---

## Task 6: Final verification

**Files:** none (verification only)

- [ ] **Step 1: Full backend test suite**

Run: `cd spotify_explorer && pytest -v`
Expected: all 55 tests pass.

- [ ] **Step 2: Repo-root test suite unaffected**

Run: `pytest tests -v` (from repo root)
Expected: all 18 pre-existing tests pass, unchanged.

- [ ] **Step 3: Frontend builds clean from scratch**

Run:
```bash
cd spotify_explorer/frontend
rm -rf node_modules ../static/frontend
npm install
npm run build
```
Expected: installs and builds with no errors, `spotify_explorer/static/frontend/index.html` + `assets/` regenerated.

- [ ] **Step 4: Manual smoke test (requires a human with real Spotify credentials and a browser)**

Walk the checklist in `spotify_explorer/README.md`, now against the Vue frontend: confirm all 5 tabs work, tab-switching preserves each tab's form/results (the `KeepAlive` behavior), login/logout work in both the build mode (`:5000`) and the dev mode (`:5173` with `FRONTEND_URL` set), and the missing-credentials/auth_error banners still show correctly.

- [ ] **Step 5: Confirm working tree is clean**

Run: `git status`
Expected: nothing to commit, working tree clean, all work committed on `feature/spotify-api-explorer`.
