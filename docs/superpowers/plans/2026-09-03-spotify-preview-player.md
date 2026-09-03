# Spotify Preview Player Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a play/pause button wherever a track appears in the Spotify Explorer dev tool, playing the track's `preview_url` (30s MP3 clip) through one shared, singleton audio player.

**Architecture:** A new module-scoped composable (`usePreviewPlayer.js`, same singleton pattern as the existing `useTabNavigation.js`) owns one real `<audio>` element for the whole app, so starting a new preview always stops whatever was playing. `MediaItemRow.vue` (used in 10 places across 7 tabs) and `TrackPreview.vue` (the hero track card) both grow an optional play/pause button wired to that composable. `trackSummary()` grows a `previewUrl` field so every existing call site can pass it through with a one-line addition — no new API calls, `preview_url` is already present on every Track object the app already fetches.

**Tech Stack:** Vue 3 `<script setup>`, native `HTMLAudioElement`. No backend changes, no new tests (this project has no JS test suite — verification is `npm run build` succeeding, matching every prior phase of this project).

---

## Task 1: Create `usePreviewPlayer.js` composable

**Files:**
- Create: `spotify_explorer/frontend/src/composables/usePreviewPlayer.js`

- [ ] **Step 1: Write the composable**

```js
import { ref } from "vue";

const audio = new Audio();
const playingUrl = ref(null);

audio.addEventListener("ended", () => {
  playingUrl.value = null;
});

export function usePreviewPlayer() {
  function toggle(url) {
    if (!url) return;
    if (playingUrl.value === url) {
      audio.pause();
      playingUrl.value = null;
      return;
    }
    audio.src = url;
    audio.play();
    playingUrl.value = url;
  }

  return { playingUrl, toggle };
}
```

This file has no isolated build check here — like `useTabNavigation.js` before it, it's not imported by anything yet, so a syntax error wouldn't surface until Task 4 (`MediaItemRow.vue`), the first real consumer, which does a build check.

- [ ] **Step 2: Commit**

```bash
git add spotify_explorer/frontend/src/composables/usePreviewPlayer.js
git commit -m "feat: add usePreviewPlayer composable for a shared, singleton audio player"
```

---

## Task 2: Add a `pause` icon to `Icon.vue`

**Files:**
- Modify: `spotify_explorer/frontend/src/components/Icon.vue`

- [ ] **Step 1: Add the new icon path**

In `spotify_explorer/frontend/src/components/Icon.vue`, add one entry to the `paths` object, after the existing `folder` entry:

```js
  pause: "M6 4h3v12H6V4zm5 0h3v12h-3V4z",
```

The existing `player` entry (a right-pointing triangle, added in an earlier phase) is reused as the "play" icon — no new icon needed for that state.

- [ ] **Step 2: Verify the build still succeeds**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/components/Icon.vue
git commit -m "feat: add pause icon (reuses existing player icon for the play state)"
```

---

## Task 3: Add `previewUrl` to `trackSummary()`

**Files:**
- Modify: `spotify_explorer/frontend/src/utils/spotifyShapes.js`

- [ ] **Step 1: Add the field**

In `spotify_explorer/frontend/src/utils/spotifyShapes.js`, replace `trackSummary`:

```js
export function trackSummary(track) {
  if (!track || !track.name) return null;
  return {
    image: track.album?.images?.[0]?.url ?? null,
    title: track.name,
    subtitle: asArray(track.artists).map((a) => a.name).join(", "),
    url: spotifyUrl(track),
    previewUrl: track.preview_url ?? null,
  };
}
```

Only `trackSummary` changes — `artistSummary`, `albumSummary`, and `playlistSummary` are untouched (Spotify doesn't return audio previews for those object types).

- [ ] **Step 2: Verify the build still succeeds**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/utils/spotifyShapes.js
git commit -m "feat: add previewUrl field to trackSummary"
```

---

## Task 4: Add the play/pause button to `MediaItemRow.vue`

**Files:**
- Modify: `spotify_explorer/frontend/src/components/MediaItemRow.vue`

- [ ] **Step 1: Replace the full file**

```vue
<script setup>
import Icon from "./Icon.vue";
import { usePreviewPlayer } from "../composables/usePreviewPlayer.js";

defineProps({
  image: { type: String, default: null },
  title: { type: String, required: true },
  subtitle: { type: String, default: "" },
  url: { type: String, default: null },
  previewUrl: { type: String, default: null },
});

const { playingUrl, toggle } = usePreviewPlayer();
</script>

<template>
  <div class="media-item-row">
    <img v-if="image" :src="image" :alt="title" class="media-item-image">
    <div v-else class="media-item-image"></div>
    <div class="media-item-info">
      <div class="media-item-title">{{ title }}</div>
      <div v-if="subtitle" class="media-item-subtitle">{{ subtitle }}</div>
    </div>
    <button
      v-if="previewUrl"
      type="button"
      class="media-item-link"
      :aria-label="playingUrl === previewUrl ? 'Pausar prévia' : 'Tocar prévia (30s)'"
      @click.stop="toggle(previewUrl)"
    >
      <Icon :name="playingUrl === previewUrl ? 'pause' : 'player'" :size="16" />
    </button>
    <a v-if="url" :href="url" target="_blank" rel="noopener" class="media-item-link" aria-label="Abrir no Spotify" @click.stop>
      <Icon name="external-link" :size="16" />
    </a>
  </div>
</template>
```

The only changes vs. the current file: the `usePreviewPlayer` import, the new `previewUrl` prop, the `{ playingUrl, toggle }` destructure, and the new `<button>` block (placed between the info block and the existing external-link `<a>`). `@click.stop` on the new button is essential — `MediaItemRow` is wrapped in a `<button class="media-item-clickable">` in the Seguindo/Minhas Playlists tabs (added in an earlier phase for cross-tab navigation); without `.stop`, clicking play would also trigger that row's navigation.

- [ ] **Step 2: Verify the build still succeeds**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/components/MediaItemRow.vue
git commit -m "feat: add play/pause button to MediaItemRow when previewUrl is present"
```

---

## Task 5: Add the play/pause button to `TrackPreview.vue`

**Files:**
- Modify: `spotify_explorer/frontend/src/components/previews/TrackPreview.vue`

- [ ] **Step 1: Replace the full file**

```vue
<script setup>
import { computed } from "vue";
import { trackSummary } from "../../utils/spotifyShapes.js";
import { usePreviewPlayer } from "../../composables/usePreviewPlayer.js";
import Icon from "../Icon.vue";

const props = defineProps({
  track: { type: Object, default: null },
  audioFeatures: { type: Object, default: null },
});

const summary = computed(() => trackSummary(props.track));
const { playingUrl, toggle } = usePreviewPlayer();

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
      <button v-if="track.preview_url" type="button" class="preview-spotify-link" @click="toggle(track.preview_url)">
        <Icon :name="playingUrl === track.preview_url ? 'pause' : 'player'" :size="14" />
        {{ playingUrl === track.preview_url ? "Pausar prévia" : "Tocar prévia (30s)" }}
      </button>
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

The only changes vs. the current file: the `usePreviewPlayer` import, the `{ playingUrl, toggle }` destructure, and the new `<button class="preview-spotify-link">` placed right after the existing "Abrir no Spotify" link — everything else (`hasFeatures`, `features`, `formatDuration`, the popularity/audio-feature bars) is unchanged. No `@click.stop` needed here — `TrackPreview` is used standalone (Track & Audio tab, Player tab's "now playing" block), never wrapped in a clickable navigation row.

- [ ] **Step 2: Verify the build still succeeds**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/components/previews/TrackPreview.vue
git commit -m "feat: add play/pause button to TrackPreview when preview_url is present"
```

---

## Task 6: Wire `previewUrl` into `SearchTab.vue`

**Files:**
- Modify: `spotify_explorer/frontend/src/tabs/SearchTab.vue`

- [ ] **Step 1: Add the prop**

In `spotify_explorer/frontend/src/tabs/SearchTab.vue`, change:

```html
          <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" />
```

to:

```html
          <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" :preview-url="item.previewUrl" />
```

`item` here comes from `summaryFn[submittedType.value]`, which can be `trackSummary`, `artistSummary`, or `albumSummary` depending on the search type — only `trackSummary` results have a `previewUrl` field; for artist/album results it's `undefined`, and the button in `MediaItemRow` (from Task 4) simply won't render, no branching needed here.

- [ ] **Step 2: Verify the build still succeeds**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/SearchTab.vue
git commit -m "feat: pass previewUrl through to MediaItemRow in Search tab"
```

---

## Task 7: Wire `previewUrl` into `RecommendationsTab.vue`

**Files:**
- Modify: `spotify_explorer/frontend/src/tabs/RecommendationsTab.vue`

- [ ] **Step 1: Add the prop**

In `spotify_explorer/frontend/src/tabs/RecommendationsTab.vue`, change:

```html
          <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" />
```

to:

```html
          <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" :preview-url="item.previewUrl" />
```

- [ ] **Step 2: Verify the build still succeeds**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/RecommendationsTab.vue
git commit -m "feat: pass previewUrl through to MediaItemRow in Recommendations tab"
```

---

## Task 8: Wire `previewUrl` into `ArtistTab.vue`

**Files:**
- Modify: `spotify_explorer/frontend/src/tabs/ArtistTab.vue`

- [ ] **Step 1: Add the prop to both `MediaItemRow` usages**

In `spotify_explorer/frontend/src/tabs/ArtistTab.vue`, there are two `<MediaItemRow>` usages — one for `topTracksItems` (tracks — will show the button), one for `relatedArtistsItems` (artists — `previewUrl` will be `undefined`, button never renders, but pass it anyway for consistency, it's harmless).

Change:

```html
          <div v-for="(item, i) in topTracksItems" :key="i">
            <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" />
          </div>
```

to:

```html
          <div v-for="(item, i) in topTracksItems" :key="i">
            <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" :preview-url="item.previewUrl" />
          </div>
```

Change:

```html
          <div v-for="(item, i) in relatedArtistsItems" :key="i">
            <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" />
          </div>
```

to:

```html
          <div v-for="(item, i) in relatedArtistsItems" :key="i">
            <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" :preview-url="item.previewUrl" />
          </div>
```

- [ ] **Step 2: Verify the build still succeeds**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/ArtistTab.vue
git commit -m "feat: pass previewUrl through to MediaItemRow in Artist tab"
```

---

## Task 9: Wire `previewUrl` into `AlbumTab.vue`

**Files:**
- Modify: `spotify_explorer/frontend/src/tabs/AlbumTab.vue`

- [ ] **Step 1: Add the prop**

In `spotify_explorer/frontend/src/tabs/AlbumTab.vue`, change:

```html
          <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" />
```

to:

```html
          <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" :preview-url="item.previewUrl" />
```

- [ ] **Step 2: Verify the build still succeeds**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/AlbumTab.vue
git commit -m "feat: pass previewUrl through to MediaItemRow in Album tab"
```

---

## Task 10: Wire `previewUrl` into `PlaylistTab.vue`

**Files:**
- Modify: `spotify_explorer/frontend/src/tabs/PlaylistTab.vue`

- [ ] **Step 1: Add the prop**

In `spotify_explorer/frontend/src/tabs/PlaylistTab.vue`, change:

```html
          <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" />
```

to:

```html
          <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" :preview-url="item.previewUrl" />
```

- [ ] **Step 2: Verify the build still succeeds**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/PlaylistTab.vue
git commit -m "feat: pass previewUrl through to MediaItemRow in Playlist tab"
```

---

## Task 11: Wire `previewUrl` into `MeusDadosTab.vue`

**Files:**
- Modify: `spotify_explorer/frontend/src/tabs/MeusDadosTab.vue`

- [ ] **Step 1: Add the prop to all three `MediaItemRow` usages**

In `spotify_explorer/frontend/src/tabs/MeusDadosTab.vue`, there are three `<MediaItemRow>` usages: `topItems` (top tracks/artists — tracks show the button, artists don't), `savedItems` (liked tracks), `recentlyPlayedItems` (recently played tracks).

Change:

```html
            <div v-for="(item, i) in topItems" :key="i">
              <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" />
            </div>
```

to:

```html
            <div v-for="(item, i) in topItems" :key="i">
              <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" :preview-url="item.previewUrl" />
            </div>
```

Change:

```html
            <div v-for="(item, i) in savedItems" :key="i">
              <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" />
            </div>
```

to:

```html
            <div v-for="(item, i) in savedItems" :key="i">
              <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" :preview-url="item.previewUrl" />
            </div>
```

Change:

```html
            <div v-for="(item, i) in recentlyPlayedItems" :key="i">
              <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" />
            </div>
```

to:

```html
            <div v-for="(item, i) in recentlyPlayedItems" :key="i">
              <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" :preview-url="item.previewUrl" />
            </div>
```

- [ ] **Step 2: Verify the build still succeeds**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/MeusDadosTab.vue
git commit -m "feat: pass previewUrl through to MediaItemRow in Meus Dados tab"
```

---

## Task 12: Wire `previewUrl` into `PlayerTab.vue`

**Files:**
- Modify: `spotify_explorer/frontend/src/tabs/PlayerTab.vue`

- [ ] **Step 1: Add the prop**

In `spotify_explorer/frontend/src/tabs/PlayerTab.vue`, change:

```html
            <div v-for="(item, i) in queueItems" :key="i">
              <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" />
            </div>
```

to:

```html
            <div v-for="(item, i) in queueItems" :key="i">
              <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" :preview-url="item.previewUrl" />
            </div>
```

`TrackPreview` (used above the queue for the "now playing" track, already updated in Task 5) needs no change here — it reads `track.preview_url` directly off the raw track object it already receives, not through `trackSummary()`.

- [ ] **Step 2: Verify the build still succeeds**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/PlayerTab.vue
git commit -m "feat: pass previewUrl through to MediaItemRow in Player tab's queue"
```

---

## Task 13: Final verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full frontend build**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds with no errors

- [ ] **Step 2: Run the full backend test suite (regression check — no backend files changed)**

Run: `cd spotify_explorer && pytest -v`
Expected: all tests pass (this plan makes no backend changes, so this should be identical to before)

- [ ] **Step 3: Manual smoke test**

Start the backend (`cd spotify_explorer && python app.py`) and frontend dev server (`cd spotify_explorer/frontend && npm run dev`), open `http://127.0.0.1:5173`. Search for a well-known track (e.g. query "Blinding Lights") and check whether a play button appears on the result row. Try the Track & Audio tab with a known track ID and check the same on the big preview card. Given the Nov/2024 `preview_url` restriction described in the spec, the most likely outcome is that no play button appears anywhere — if so, that confirms the restriction in practice for this app; if a button DOES appear somewhere, click it and confirm: (a) audio actually plays, (b) the icon swaps to pause while playing, (c) clicking a second track's play button stops the first and starts the second, (d) the icon reverts to play when the clip ends naturally.
