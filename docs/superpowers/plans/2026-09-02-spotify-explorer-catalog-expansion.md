# Spotify Explorer Catalog Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 3 new catalog tabs (Album, Playlist, New Releases) to `spotify_explorer`'s frontend and polish the 5 existing tabs with data the Spotify API already returns but currently only shows in the raw JSON — a "Abrir no Spotify" link on every list/preview item, and popularity/explicit metadata on the Track/Artist hero cards.

**Architecture:** 3 small, Client-Credentials-only Flask routes (no new OAuth scope, no login) mirroring the existing catalog routes exactly. On the frontend: `spotifyShapes.js` gains a `url` field on every `*Summary()` return value plus a new `playlistSummary()`; `MediaItemRow.vue` gains an opt-in `url` prop; `TrackPreview.vue`/`ArtistPreview.vue` gain a popularity bar + Spotify link (reusing existing CSS patterns); 2 new preview components (`AlbumPreview.vue`, `PlaylistPreview.vue`) and 3 new tabs follow the exact same `useApi()` + `ResultPanel` + `useHistory` pattern already established by `SearchTab.vue`/`RecommendationsTab.vue`.

**Tech Stack:** Same as the rest of `spotify_explorer` — Flask/pytest backend, Vue 3 (Composition API, `<script setup>`) frontend, no new npm dependencies, no JS test framework (verification via `npm run build` + backend pytest).

**Spec:** `docs/superpowers/specs/2026-09-02-spotify-explorer-catalog-expansion.md`

---

## Task 1: Backend — Album, Playlist, New Releases routes

**Files:**
- Modify: `spotify_explorer/app.py`
- Modify: `spotify_explorer/test_app.py`

- [ ] **Step 1: Add the failing tests**

Append to `spotify_explorer/test_app.py`:

```python
def test_album_calls_correct_path(client, monkeypatch):
    def fake_api_get(path, client_id, client_secret, params=None):
        assert path == "/albums/album1"
        return {"name": "Test Album"}, 200

    monkeypatch.setattr(app_module.spotify_client, "api_get", fake_api_get)

    response = client.get("/api/album/album1")

    assert response.status_code == 200
    assert response.get_json() == {"name": "Test Album"}


def test_playlist_calls_correct_path(client, monkeypatch):
    def fake_api_get(path, client_id, client_secret, params=None):
        assert path == "/playlists/playlist1"
        return {"name": "Test Playlist"}, 200

    monkeypatch.setattr(app_module.spotify_client, "api_get", fake_api_get)

    response = client.get("/api/playlist/playlist1")

    assert response.status_code == 200
    assert response.get_json() == {"name": "Test Playlist"}


def test_new_releases_forwards_limit_param(client, monkeypatch):
    def fake_api_get(path, client_id, client_secret, params=None):
        assert path == "/browse/new-releases"
        assert params == {"limit": "5"}
        return {"albums": {"items": []}}, 200

    monkeypatch.setattr(app_module.spotify_client, "api_get", fake_api_get)

    response = client.get("/api/new-releases?limit=5")

    assert response.status_code == 200


def test_new_releases_defaults_limit_to_20(client, monkeypatch):
    def fake_api_get(path, client_id, client_secret, params=None):
        assert params["limit"] == "20"
        return {"albums": {"items": []}}, 200

    monkeypatch.setattr(app_module.spotify_client, "api_get", fake_api_get)

    response = client.get("/api/new-releases")

    assert response.status_code == 200
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd spotify_explorer && pytest test_app.py -v`
Expected: the 4 new tests FAIL with 404 (routes not defined). All 15 pre-existing tests in this file still PASS unchanged.

- [ ] **Step 3: Add the routes**

Add inside `register_routes(app)` in `spotify_explorer/app.py`, right after the `recommendations` route (after its closing `return jsonify(body), status`, before `@app.route("/login")`):

```python
    @app.route("/api/album/<album_id>")
    def album(album_id):
        body, status = spotify_client.api_get(
            f"/albums/{album_id}",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
        )
        return jsonify(body), status

    @app.route("/api/playlist/<playlist_id>")
    def playlist(playlist_id):
        body, status = spotify_client.api_get(
            f"/playlists/{playlist_id}",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
        )
        return jsonify(body), status

    @app.route("/api/new-releases")
    def new_releases():
        body, status = spotify_client.api_get(
            "/browse/new-releases",
            app.config["SPOTIFY_CLIENT_ID"],
            app.config["SPOTIFY_CLIENT_SECRET"],
            params={"limit": request.args.get("limit", "20")},
        )
        return jsonify(body), status
```

No new imports needed — `jsonify`, `request`, `spotify_client` are already imported at the top of `app.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd spotify_explorer && pytest test_app.py -v`
Expected: 19 passed (15 prior + 4 new).

Run: `cd spotify_explorer && pytest -v`
Expected: all 59 tests pass (current total is 55; this task's 4 new tests bring it to 59).

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/app.py spotify_explorer/test_app.py
git commit -m "feat: add /api/album, /api/playlist, /api/new-releases routes"
```

---

## Task 2: Polish infrastructure — `url` on every summary, `MediaItemRow`'s link icon, new icons

**Files:**
- Modify: `spotify_explorer/frontend/src/utils/spotifyShapes.js`
- Modify: `spotify_explorer/frontend/src/components/MediaItemRow.vue`
- Modify: `spotify_explorer/frontend/src/components/Icon.vue`
- Modify: `spotify_explorer/frontend/src/style.css`
- Modify: `spotify_explorer/frontend/src/tabs/SearchTab.vue`
- Modify: `spotify_explorer/frontend/src/tabs/RecommendationsTab.vue`
- Modify: `spotify_explorer/frontend/src/tabs/ArtistTab.vue`
- Modify: `spotify_explorer/frontend/src/tabs/MeusDadosTab.vue`

This task wires the "Abrir no Spotify" link end-to-end for every list row across the app, and adds the icons the new tabs (Tasks 4-6) will need. No new tabs yet.

- [ ] **Step 1: Replace `spotifyShapes.js`**

Replace the entire contents of `spotify_explorer/frontend/src/utils/spotifyShapes.js` with:

```javascript
function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function spotifyUrl(obj) {
  return obj?.external_urls?.spotify ?? null;
}

export function trackSummary(track) {
  if (!track || !track.name) return null;
  return {
    image: track.album?.images?.[0]?.url ?? null,
    title: track.name,
    subtitle: asArray(track.artists).map((a) => a.name).join(", "),
    url: spotifyUrl(track),
  };
}

export function artistSummary(artist) {
  if (!artist || !artist.name) return null;
  return {
    image: artist.images?.[0]?.url ?? null,
    title: artist.name,
    subtitle:
      artist.followers?.total != null
        ? `${artist.followers.total.toLocaleString("pt-BR")} seguidores`
        : asArray(artist.genres).join(", "),
    url: spotifyUrl(artist),
  };
}

export function albumSummary(album) {
  if (!album || !album.name) return null;
  return {
    image: album.images?.[0]?.url ?? null,
    title: album.name,
    subtitle: asArray(album.artists).map((a) => a.name).join(", "),
    url: spotifyUrl(album),
  };
}

export function playlistSummary(playlist) {
  if (!playlist || !playlist.name) return null;
  return {
    image: playlist.images?.[0]?.url ?? null,
    title: playlist.name,
    subtitle: playlist.owner?.display_name ? `por ${playlist.owner.display_name}` : "",
    url: spotifyUrl(playlist),
  };
}
```

Changes from the current file: a new `spotifyUrl(obj)` helper, a `url` field added to `trackSummary`/`artistSummary`/`albumSummary`'s return objects, and a brand-new `playlistSummary` function (used starting Task 5). `asArray` and every existing field are unchanged.

- [ ] **Step 2: Replace `MediaItemRow.vue`**

```vue
<script setup>
import Icon from "./Icon.vue";

defineProps({
  image: { type: String, default: null },
  title: { type: String, required: true },
  subtitle: { type: String, default: "" },
  url: { type: String, default: null },
});
</script>

<template>
  <div class="media-item-row">
    <img v-if="image" :src="image" :alt="title" class="media-item-image">
    <div v-else class="media-item-image"></div>
    <div class="media-item-info">
      <div class="media-item-title">{{ title }}</div>
      <div v-if="subtitle" class="media-item-subtitle">{{ subtitle }}</div>
    </div>
    <a v-if="url" :href="url" target="_blank" rel="noopener" class="media-item-link" aria-label="Abrir no Spotify">
      <Icon name="external-link" :size="16" />
    </a>
  </div>
</template>
```

New: `url` prop (default `null`, so every existing call site that doesn't pass it renders identically to before), a new `.media-item-info` wrapper div around the title/subtitle (needed so the link icon can be pushed to the row's right edge via flexbox — see Step 4's CSS), and the conditional link itself.

- [ ] **Step 3: Add 4 new icons to `Icon.vue`**

Add these 4 entries to the `paths` object in `spotify_explorer/frontend/src/components/Icon.vue` (anywhere inside the object, e.g. right after `logout`):

```javascript
  "external-link": "M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5zM5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 100-2H5z",
  album: "M4 3a1 1 0 00-1 1v3a1 1 0 001 1h3a1 1 0 001-1V4a1 1 0 00-1-1H4zm9 0a1 1 0 00-1 1v3a1 1 0 001 1h3a1 1 0 001-1V4a1 1 0 00-1-1h-3zM4 12a1 1 0 00-1 1v3a1 1 0 001 1h3a1 1 0 001-1v-3a1 1 0 00-1-1H4zm9 0a1 1 0 00-1 1v3a1 1 0 001 1h3a1 1 0 001-1v-3a1 1 0 00-1-1h-3z",
  playlist: "M3 5a1 1 0 011-1h8a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h8a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h5a1 1 0 110 2H4a1 1 0 01-1-1zm13-9a2 2 0 100 4 2 2 0 000-4z",
  "new-releases": "M10 2l2.163 4.382 4.837.703-3.5 3.412.826 4.815L10 13.033l-4.326 2.279.826-4.815-3.5-3.412 4.837-.703L10 2z",
```

Note the quoted keys (`"external-link"`, `"new-releases"`) — required since these names contain a hyphen, unlike the existing unquoted keys (`search`, `disc`, etc.), which are valid JS identifiers on their own. Nothing else in the file changes.

- [ ] **Step 4: Append new CSS to `style.css`**

Add this block to the end of `spotify_explorer/frontend/src/style.css`:

```css
.media-item-info {
  flex: 1;
  min-width: 0;
}

.media-item-link {
  display: flex;
  align-items: center;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.media-item-link:hover {
  color: var(--accent);
}
```

- [ ] **Step 5: Wire `:url="item.url"` into every existing `MediaItemRow` usage**

In each of these 4 files, find every line that reads exactly:
```html
<MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" />
```
and replace it with:
```html
<MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" />
```

Files and occurrence counts (verify each after editing — don't leave any unchanged):
- `spotify_explorer/frontend/src/tabs/SearchTab.vue` — 1 occurrence
- `spotify_explorer/frontend/src/tabs/RecommendationsTab.vue` — 1 occurrence
- `spotify_explorer/frontend/src/tabs/ArtistTab.vue` — 2 occurrences (top tracks list, related artists list)
- `spotify_explorer/frontend/src/tabs/MeusDadosTab.vue` — 3 occurrences (top tracks/artists, saved tracks, recently played)

This works because `item` in every one of these `v-for` loops is already the object returned by a `*Summary()` function, which now includes `url` per Step 1 — no other change needed in these 4 files (no new imports, no computed changes, nothing else).

- [ ] **Step 6: Verify**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: builds without errors.

Run: `cd spotify_explorer && pytest -v`
Expected: all 59 tests pass.

- [ ] **Step 7: Commit**

```bash
git add spotify_explorer/frontend/src/utils/spotifyShapes.js spotify_explorer/frontend/src/components/MediaItemRow.vue spotify_explorer/frontend/src/components/Icon.vue spotify_explorer/frontend/src/style.css spotify_explorer/frontend/src/tabs/SearchTab.vue spotify_explorer/frontend/src/tabs/RecommendationsTab.vue spotify_explorer/frontend/src/tabs/ArtistTab.vue spotify_explorer/frontend/src/tabs/MeusDadosTab.vue
git commit -m "feat: add \"Abrir no Spotify\" link to every list row, add icons for upcoming tabs"
```

---

## Task 3: Polish `TrackPreview.vue` and `ArtistPreview.vue` — popularity, explicit badge, Spotify link

**Files:**
- Modify: `spotify_explorer/frontend/src/components/previews/TrackPreview.vue`
- Modify: `spotify_explorer/frontend/src/components/previews/ArtistPreview.vue`
- Modify: `spotify_explorer/frontend/src/style.css`

- [ ] **Step 1: Append new CSS to `style.css`**

Add this block to the end of `spotify_explorer/frontend/src/style.css`:

```css
.preview-explicit-badge {
  display: inline-block;
  margin-left: 0.5rem;
  padding: 0.1rem 0.4rem;
  border-radius: 3px;
  background: var(--bg-elevated-hover);
  color: var(--text-secondary);
  font-size: 0.65rem;
  font-weight: 700;
  vertical-align: middle;
}

.preview-spotify-link {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  margin-top: 0.5rem;
  color: var(--accent);
  font-size: 0.85rem;
  font-weight: 700;
  text-decoration: none;
}

.preview-spotify-link:hover {
  text-decoration: underline;
}
```

- [ ] **Step 2: Replace `TrackPreview.vue`**

```vue
<script setup>
import { computed } from "vue";
import { trackSummary } from "../../utils/spotifyShapes.js";
import Icon from "../Icon.vue";

const props = defineProps({
  track: { type: Object, default: null },
  audioFeatures: { type: Object, default: null },
});

const summary = computed(() => trackSummary(props.track));

const hasFeatures = computed(
  () => props.audioFeatures && typeof props.audioFeatures.danceability === "number"
);

const features = [
  { key: "danceability", label: "Danceability" },
  { key: "energy", label: "Energy" },
  { key: "valence", label: "Valence" },
];

function formatDuration(ms) {
  if (!ms) return "";
  const totalSeconds = Math.round(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}
</script>

<template>
  <div v-if="summary" class="preview-card">
    <img v-if="summary.image" :src="summary.image" :alt="summary.title" class="preview-image">
    <div>
      <div class="preview-title">
        {{ summary.title }}
        <span v-if="track.explicit" class="preview-explicit-badge">Explicit</span>
      </div>
      <div class="preview-subtitle">{{ summary.subtitle }}</div>
      <div v-if="track.duration_ms" class="preview-subtitle">{{ formatDuration(track.duration_ms) }}</div>
      <a v-if="summary.url" :href="summary.url" target="_blank" rel="noopener" class="preview-spotify-link">
        <Icon name="external-link" :size="14" />
        Abrir no Spotify
      </a>
      <div v-if="typeof track.popularity === 'number'" class="audio-feature-bar">
        <span>Popularidade</span>
        <div class="audio-feature-track">
          <div class="audio-feature-fill" :style="{ width: `${track.popularity}%` }"></div>
        </div>
        <span>{{ track.popularity }}%</span>
      </div>
      <div v-if="hasFeatures">
        <div v-for="feature in features" :key="feature.key" class="audio-feature-bar">
          <span>{{ feature.label }}</span>
          <div class="audio-feature-track">
            <div class="audio-feature-fill" :style="{ width: `${audioFeatures[feature.key] * 100}%` }"></div>
          </div>
          <span>{{ Math.round(audioFeatures[feature.key] * 100) }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>
```

Note the popularity bar reuses the existing `.audio-feature-bar`/`.audio-feature-track`/`.audio-feature-fill` classes (already styled from an earlier task) — popularity is already a 0-100 integer from Spotify, so the fill width is `${track.popularity}%` directly, unlike `danceability`/`energy`/`valence` which are 0-1 floats requiring `* 100`. Don't try to unify these into one loop — the different scales make a small amount of duplication clearer than a shared abstraction here.

- [ ] **Step 3: Replace `ArtistPreview.vue`**

```vue
<script setup>
import { computed } from "vue";
import { artistSummary } from "../../utils/spotifyShapes.js";
import Icon from "../Icon.vue";

const props = defineProps({
  artist: { type: Object, default: null },
});

const summary = computed(() => artistSummary(props.artist));
</script>

<template>
  <div v-if="summary" class="preview-card">
    <img v-if="summary.image" :src="summary.image" :alt="summary.title" class="preview-image">
    <div>
      <div class="preview-title">{{ summary.title }}</div>
      <div class="preview-subtitle">{{ summary.subtitle }}</div>
      <div v-if="artist.genres?.length" class="preview-genres">
        <span v-for="genre in artist.genres" :key="genre" class="preview-genre-chip">{{ genre }}</span>
      </div>
      <a v-if="summary.url" :href="summary.url" target="_blank" rel="noopener" class="preview-spotify-link">
        <Icon name="external-link" :size="14" />
        Abrir no Spotify
      </a>
      <div v-if="typeof artist.popularity === 'number'" class="audio-feature-bar">
        <span>Popularidade</span>
        <div class="audio-feature-track">
          <div class="audio-feature-fill" :style="{ width: `${artist.popularity}%` }"></div>
        </div>
        <span>{{ artist.popularity }}%</span>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 4: Verify**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: builds without errors.

Run: `cd spotify_explorer && pytest -v`
Expected: all 59 tests pass.

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/frontend/src/components/previews/TrackPreview.vue spotify_explorer/frontend/src/components/previews/ArtistPreview.vue spotify_explorer/frontend/src/style.css
git commit -m "feat: add popularity bar, explicit badge, and Spotify link to Track/Artist previews"
```

---

## Task 4: `AlbumPreview.vue` and `AlbumTab.vue`

**Files:**
- Create: `spotify_explorer/frontend/src/components/previews/AlbumPreview.vue`
- Create: `spotify_explorer/frontend/src/tabs/AlbumTab.vue`

- [ ] **Step 1: Create `AlbumPreview.vue`**

Hero card only (cover, name, artist(s), release date, track count, Spotify link) — the track list itself is rendered by `AlbumTab.vue`, not this component, matching the `ArtistPreview.vue`/`ArtistTab.vue` split already established (the preview component is just the "header" card; list rendering stays in the tab):

```vue
<script setup>
import { computed } from "vue";
import { albumSummary } from "../../utils/spotifyShapes.js";
import Icon from "../Icon.vue";

const props = defineProps({
  album: { type: Object, default: null },
});

const summary = computed(() => albumSummary(props.album));
</script>

<template>
  <div v-if="summary" class="preview-card">
    <img v-if="summary.image" :src="summary.image" :alt="summary.title" class="preview-image">
    <div>
      <div class="preview-title">{{ summary.title }}</div>
      <div class="preview-subtitle">{{ summary.subtitle }}</div>
      <div v-if="album.release_date" class="preview-subtitle">{{ album.release_date }}</div>
      <div v-if="album.total_tracks" class="preview-subtitle">{{ album.total_tracks }} faixas</div>
      <a v-if="summary.url" :href="summary.url" target="_blank" rel="noopener" class="preview-spotify-link">
        <Icon name="external-link" :size="14" />
        Abrir no Spotify
      </a>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Create `AlbumTab.vue`**

A single-call tab (like `SearchTab.vue`/`RecommendationsTab.vue` — uses `useApi()` directly, not the manual `Promise.all` pattern `TrackTab.vue`/`ArtistTab.vue` use, since fetching an album is exactly one backend call):

```vue
<script setup>
import { computed, reactive, ref } from "vue";
import { useApi } from "../composables/useApi.js";
import { useHistory } from "../composables/useHistory.js";
import { trackSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import AlbumPreview from "../components/previews/AlbumPreview.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const albumId = ref("");
const { status, call } = useApi();
const result = reactive({ data: null });
const { items: history, add: addToHistory } = useHistory("album");

const tracks = computed(() => {
  const items = result.data?.tracks?.items;
  if (!Array.isArray(items)) return [];
  return items.map(trackSummary).filter((item) => item !== null);
});

async function onSubmit() {
  const { data } = await call(`/api/album/${albumId.value}`);
  result.data = data;
  addToHistory(albumId.value);
}
</script>

<template>
  <section>
    <h2>Album</h2>
    <div v-if="history.length" class="history-chips">
      <button v-for="item in history" :key="item" type="button" class="history-chip" @click="albumId = item">
        {{ item }}
      </button>
    </div>
    <form @submit.prevent="onSubmit">
      <label>Album ID <input type="text" v-model="albumId" required placeholder="ex: 4aawyAB9vmqN3uQ7FjRGTy"></label>
      <button type="submit" class="btn">Buscar álbum</button>
    </form>
    <ResultPanel :status="status" :data="result.data" empty-hint="Cole um Album ID, ex: 4aawyAB9vmqN3uQ7FjRGTy">
      <template #preview>
        <AlbumPreview :album="result.data" />
        <div v-if="tracks.length">
          <h3>Faixas</h3>
          <div v-for="(item, i) in tracks" :key="i">
            <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" />
          </div>
        </div>
      </template>
    </ResultPanel>
  </section>
</template>
```

`GET /albums/{id}` returns the album object with `tracks.items[]` embedded directly (each a simplified track object — notably WITHOUT its own `.album` field, since it's redundant inside an album response) — so `trackSummary` will return `image: null` for every track in this list (there's no per-track cover to show, which is fine and expected: `MediaItemRow` already renders a placeholder for a null image, and the album's own cover is already shown once at the top via `AlbumPreview`). `result.data` is passed directly as the `album` prop to `AlbumPreview` since the backend route returns the raw album object with no wrapper.

- [ ] **Step 3: Verify**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: builds without errors.

Run: `cd spotify_explorer && pytest -v`
Expected: all 59 tests pass.

- [ ] **Step 4: Commit**

```bash
git add spotify_explorer/frontend/src/components/previews/AlbumPreview.vue spotify_explorer/frontend/src/tabs/AlbumTab.vue
git commit -m "feat: add Album tab with AlbumPreview and track list"
```

---

## Task 5: `PlaylistPreview.vue` and `PlaylistTab.vue`

**Files:**
- Create: `spotify_explorer/frontend/src/components/previews/PlaylistPreview.vue`
- Create: `spotify_explorer/frontend/src/tabs/PlaylistTab.vue`

- [ ] **Step 1: Create `PlaylistPreview.vue`**

```vue
<script setup>
import { computed } from "vue";
import { playlistSummary } from "../../utils/spotifyShapes.js";
import Icon from "../Icon.vue";

const props = defineProps({
  playlist: { type: Object, default: null },
});

const summary = computed(() => playlistSummary(props.playlist));
</script>

<template>
  <div v-if="summary" class="preview-card">
    <img v-if="summary.image" :src="summary.image" :alt="summary.title" class="preview-image">
    <div>
      <div class="preview-title">{{ summary.title }}</div>
      <div class="preview-subtitle">{{ summary.subtitle }}</div>
      <div v-if="playlist.description" class="preview-subtitle">{{ playlist.description }}</div>
      <div v-if="playlist.tracks?.total != null" class="preview-subtitle">{{ playlist.tracks.total }} faixas</div>
      <a v-if="summary.url" :href="summary.url" target="_blank" rel="noopener" class="preview-spotify-link">
        <Icon name="external-link" :size="14" />
        Abrir no Spotify
      </a>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Create `PlaylistTab.vue`**

Same single-call shape as `AlbumTab.vue`. Playlist tracks come back as `tracks.items[] = [{track: {...}, added_at, ...}]` — the same "wrapped" shape already handled in `MeusDadosTab.vue` for saved tracks and recently-played, so `item.track` needs to be unwrapped before summarizing (unlike `AlbumTab.vue`, where album tracks are bare objects, not wrapped):

```vue
<script setup>
import { computed, reactive, ref } from "vue";
import { useApi } from "../composables/useApi.js";
import { useHistory } from "../composables/useHistory.js";
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
</script>

<template>
  <section>
    <h2>Playlist</h2>
    <div v-if="history.length" class="history-chips">
      <button v-for="item in history" :key="item" type="button" class="history-chip" @click="playlistId = item">
        {{ item }}
      </button>
    </div>
    <form @submit.prevent="onSubmit">
      <label>Playlist ID <input type="text" v-model="playlistId" required placeholder="ex: 37i9dQZF1DXcBWIGoYBM5M"></label>
      <button type="submit" class="btn">Buscar playlist</button>
    </form>
    <ResultPanel
      :status="status"
      :data="result.data"
      empty-hint="Cole um Playlist ID de uma playlist pública, ex: 37i9dQZF1DXcBWIGoYBM5M"
    >
      <template #preview>
        <PlaylistPreview :playlist="result.data" />
        <div v-if="tracks.length">
          <h3>Faixas</h3>
          <div v-for="(item, i) in tracks" :key="i">
            <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" />
          </div>
        </div>
      </template>
    </ResultPanel>
  </section>
</template>
```

Only PUBLIC playlists work here — the backend uses Client Credentials (app-only auth), which cannot see a private or collaborative playlist belonging to some other user; Spotify returns a 403/404 in that case, and the tool shows it exactly like any other error (no special-casing).

- [ ] **Step 3: Verify**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: builds without errors.

Run: `cd spotify_explorer && pytest -v`
Expected: all 59 tests pass.

- [ ] **Step 4: Commit**

```bash
git add spotify_explorer/frontend/src/components/previews/PlaylistPreview.vue spotify_explorer/frontend/src/tabs/PlaylistTab.vue
git commit -m "feat: add Playlist tab with PlaylistPreview and track list"
```

---

## Task 6: `NewReleasesTab.vue`

**Files:**
- Create: `spotify_explorer/frontend/src/tabs/NewReleasesTab.vue`

No preview card needed — this tab is just a flat list of albums, same shape as `SearchTab.vue`'s list rendering. No ID field either (unlike every other catalog tab so far) — just a limit input and a button, matching the button-triggered sections already used in `MeusDadosTab.vue`. No history chips either, for the same reason `MeusDadosTab.vue` has none — there's no free-text field to remember.

- [ ] **Step 1: Create the file**

```vue
<script setup>
import { computed, reactive } from "vue";
import { useApi } from "../composables/useApi.js";
import { albumSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const form = reactive({ limit: 20 });
const { status, call } = useApi();
const result = reactive({ data: null });

const items = computed(() => {
  if (!result.data?.albums?.items) return [];
  return result.data.albums.items.map(albumSummary).filter((item) => item !== null);
});

async function onSubmit() {
  const { data } = await call(`/api/new-releases?limit=${Number(form.limit)}`);
  result.data = data;
}
</script>

<template>
  <section>
    <h2>New Releases</h2>
    <form @submit.prevent="onSubmit">
      <label>Limit <input type="number" v-model.number="form.limit" min="1" max="50"></label>
      <button type="submit" class="btn">Buscar lançamentos</button>
    </form>
    <ResultPanel :status="status" :data="result.data" empty-hint="Clique em Buscar lançamentos">
      <template #preview>
        <div v-for="(item, i) in items" :key="i">
          <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" />
        </div>
      </template>
    </ResultPanel>
  </section>
</template>
```

- [ ] **Step 2: Verify**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: builds without errors.

Run: `cd spotify_explorer && pytest -v`
Expected: all 59 tests pass.

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/NewReleasesTab.vue
git commit -m "feat: add New Releases tab"
```

---

## Task 7: Wire the 3 new tabs into `App.vue`

**Files:**
- Modify: `spotify_explorer/frontend/src/App.vue`

`AppSidebar.vue` needs no changes — it already renders whatever `tabs` array `App.vue` gives it.

- [ ] **Step 1: Add the 3 imports**

In `spotify_explorer/frontend/src/App.vue`, add these 3 lines to the existing block of tab imports (after `import MeusDadosTab from "./tabs/MeusDadosTab.vue";`):

```javascript
import AlbumTab from "./tabs/AlbumTab.vue";
import PlaylistTab from "./tabs/PlaylistTab.vue";
import NewReleasesTab from "./tabs/NewReleasesTab.vue";
```

- [ ] **Step 2: Extend the `tabs` array**

Replace the `tabs` array:
```javascript
const tabs = [
  { id: "search", label: "Search", icon: "search", component: SearchTab },
  { id: "track", label: "Track & Audio", icon: "disc", component: TrackTab },
  { id: "artist", label: "Artist", icon: "mic", component: ArtistTab },
  { id: "recommendations", label: "Recommendations", icon: "sparkles", component: RecommendationsTab },
  { id: "me", label: "Meus dados", icon: "heart", component: MeusDadosTab },
];
```
with:
```javascript
const tabs = [
  { id: "search", label: "Search", icon: "search", component: SearchTab },
  { id: "track", label: "Track & Audio", icon: "disc", component: TrackTab },
  { id: "artist", label: "Artist", icon: "mic", component: ArtistTab },
  { id: "album", label: "Album", icon: "album", component: AlbumTab },
  { id: "playlist", label: "Playlist", icon: "playlist", component: PlaylistTab },
  { id: "new-releases", label: "New Releases", icon: "new-releases", component: NewReleasesTab },
  { id: "recommendations", label: "Recommendations", icon: "sparkles", component: RecommendationsTab },
  { id: "me", label: "Meus dados", icon: "heart", component: MeusDadosTab },
];
```

The 3 new entries go between `artist` and `recommendations` — grouping all the "look something up by ID" catalog tabs together (Search, Track, Artist, Album, Playlist, New Releases), with Recommendations and Meus dados staying last. Nothing else in `App.vue` changes — `activeTab`, `config`, `authError`, `useAuthStatus`, `onMounted`, and the template are all untouched.

- [ ] **Step 3: Verify**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: builds without errors.

Run: `cd spotify_explorer && pytest -v`
Expected: all 59 tests pass.

- [ ] **Step 4: Commit**

```bash
git add spotify_explorer/frontend/src/App.vue
git commit -m "feat: wire Album, Playlist, and New Releases tabs into the sidebar"
```

---

## Task 8: Update `README.md`

**Files:**
- Modify: `spotify_explorer/README.md`

- [ ] **Step 1: Extend "O que cada aba faz"**

In `spotify_explorer/README.md`, find the "## O que cada aba faz" section:

```markdown
## O que cada aba faz

- **Search** — `GET /search` do catálogo (track/artist/album)
- **Track & Audio** — `GET /tracks/{id}`, `/audio-features/{id}`,
  `/audio-analysis/{id}`
- **Artist** — `GET /artists/{id}` + top-tracks + albums + related-artists
- **Recommendations** — `GET /recommendations` com seeds e parâmetros alvo
- **Meus dados** — requer login (Authorization Code Flow): top
  tracks/artists por `time_range`, faixas curtidas, tocadas recentemente
```

Replace it with (3 new bullets added, inserted after "Artist" to match the tab order in the sidebar; every existing bullet's text is untouched):

```markdown
## O que cada aba faz

- **Search** — `GET /search` do catálogo (track/artist/album)
- **Track & Audio** — `GET /tracks/{id}`, `/audio-features/{id}`,
  `/audio-analysis/{id}`
- **Artist** — `GET /artists/{id}` + top-tracks + albums + related-artists
- **Album** — `GET /albums/{id}` (dados + faixas)
- **Playlist** — `GET /playlists/{id}` (dados + faixas — só playlists
  públicas, Client Credentials não vê playlist privada de terceiros)
- **New Releases** — `GET /browse/new-releases`
- **Recommendations** — `GET /recommendations` com seeds e parâmetros alvo
- **Meus dados** — requer login (Authorization Code Flow): top
  tracks/artists por `time_range`, faixas curtidas, tocadas recentemente
```

- [ ] **Step 2: Commit**

```bash
git add spotify_explorer/README.md
git commit -m "docs: document the Album, Playlist, and New Releases tabs"
```

---

## Task 9: Final verification

**Files:** none (verification only)

- [ ] **Step 1: Full backend test suite**

Run: `cd spotify_explorer && pytest -v`
Expected: all 59 tests pass.

- [ ] **Step 2: Repo-root test suite unaffected**

Run: `pytest tests -v` (from repo root)
Expected: all 18 pre-existing, unrelated tests pass.

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

Run `python app.py` (after `npm run build`), open the app, and confirm:
- Sidebar now shows 8 items, in order: Search, Track & Audio, Artist, Album, Playlist, New Releases, Recommendations, Meus dados
- On Search/Recommendations/Artist(top-tracks, related-artists)/Meus dados(all 3 sections): every list row now has a small external-link icon that opens the item on open.spotify.com in a new tab
- Track & Audio and Artist hero cards show a "Abrir no Spotify" link and a Popularidade bar; a track with `explicit: true` (search an explicit song) shows the "Explicit" badge
- Album: paste a real Album ID (e.g. `4aawyAB9vmqN3uQ7FjRGTy`) — hero card with cover/name/artist/release date/track count, track list below, all with working Spotify links
- Playlist: paste a real public Playlist ID (e.g. `37i9dQZF1DXcBWIGoYBM5M`) — hero card + track list; try a private playlist ID and confirm it shows a 403/404 in the JSON panel instead of crashing
- New Releases: click "Buscar lançamentos" with no ID field — a list of recent album releases appears
- All 3 new tabs preserve their form/results when switching away and back (`KeepAlive`)

## Self-Review Notes

**Spec coverage:** every item in `docs/superpowers/specs/2026-09-02-spotify-explorer-catalog-expansion.md` maps to a task — 3 backend routes (Task 1), `url` on every summary + `MediaItemRow` link icon wired into all 4 existing list-consumers (Task 2), Track/Artist popularity+explicit+link polish (Task 3), Album tab (Task 4), Playlist tab (Task 5), New Releases tab (Task 6), sidebar wiring (Task 7), README (Task 8). Phase 2 (Player, Seguindo, minhas playlists) is explicitly out of scope and untouched by any task here.

**Type/interface consistency:** `trackSummary`/`artistSummary`/`albumSummary`/`playlistSummary` all return `{image, title, subtitle, url}` or `null` — verified consistent across Tasks 2, 4, 5. `MediaItemRow` props (`image`/`title`/`subtitle`/`url`) match every call site added in Tasks 2, 4, 5, 6. `useApi()`'s `{status, call}` contract (established before this plan) is used identically by `AlbumTab.vue`/`PlaylistTab.vue`/`NewReleasesTab.vue`, matching `SearchTab.vue`/`RecommendationsTab.vue`'s existing pattern — none of these 3 new tabs need the manual `Promise.all` pattern `TrackTab.vue`/`ArtistTab.vue` use, since each only makes one backend call.
