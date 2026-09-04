# Now-Playing Modal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clicking a track row in Spotify Explorer opens a modal that simulates real playback (art, equalizer animation, progress bar, play/pause, "Abrir no Spotify") instead of the row's current tiny inline preview button and external-link icon.

**Architecture:** Two new module-scoped Vue composables (`useNowPlaying` for modal state, extending `usePreviewPlayer` with real progress) plus one new `NowPlayingModal.vue` mounted once in `App.vue`. `MediaItemRow.vue` loses its two inline buttons; 8 tab files wrap their track rows in a `<button class="media-item-clickable" @click="open(item)">`, the same pattern `FollowingTab`/`MyPlaylistsTab` already use for navigation.

**Tech Stack:** Vue 3 `<script setup>` SFCs, Vite, no JS test runner (existing project convention — verification is `npm run build` + manual browser check, same as every prior spec in this codebase).

**Spec:** [`docs/superpowers/specs/2026-09-03-now-playing-modal-design.md`](../specs/2026-09-03-now-playing-modal-design.md)

All paths below are relative to `spotify_explorer/frontend/src/`.

---

### Task 1: Add the `close` icon to `Icon.vue`

**Files:**
- Modify: `components/Icon.vue:24` (insert after the `pause` entry)

- [ ] **Step 1: Add the icon path**

In `components/Icon.vue`, the `paths` object currently ends with:

```js
  pause: "M6 4h3v12H6V4zm5 0h3v12h-3V4z",
};
```

Change it to:

```js
  pause: "M6 4h3v12H6V4zm5 0h3v12h-3V4z",
  close: "M4.3 4.3a1 1 0 011.4 0L10 8.6l4.3-4.3a1 1 0 111.4 1.4L11.4 10l4.3 4.3a1 1 0 01-1.4 1.4L10 11.4l-4.3 4.3a1 1 0 01-1.4-1.4L8.6 10 4.3 5.7a1 1 0 010-1.4z",
};
```

- [ ] **Step 2: Verify the file still parses**

Run: `cd spotify_explorer/frontend && npx vite build --logLevel warn`
Expected: build succeeds (exit code 0), no Vue/JS syntax errors mentioning `Icon.vue`.

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/components/Icon.vue
git commit -m "feat(spotify-explorer): add close icon"
```

---

### Task 2: `trackSummary()` gains `durationMs`

**Files:**
- Modify: `utils/spotifyShapes.js:9-18`

- [ ] **Step 1: Add the field**

Current:

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

Change to:

```js
export function trackSummary(track) {
  if (!track || !track.name) return null;
  return {
    image: track.album?.images?.[0]?.url ?? null,
    title: track.name,
    subtitle: asArray(track.artists).map((a) => a.name).join(", "),
    url: spotifyUrl(track),
    previewUrl: track.preview_url ?? null,
    durationMs: track.duration_ms ?? null,
  };
}
```

- [ ] **Step 2: Verify**

Run: `cd spotify_explorer/frontend && npx vite build --logLevel warn`
Expected: build succeeds.

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/utils/spotifyShapes.js
git commit -m "feat(spotify-explorer): add durationMs to trackSummary"
```

---

### Task 3: Extend `usePreviewPlayer.js` with real progress + `stop()`

**Files:**
- Modify: `composables/usePreviewPlayer.js` (whole file)

- [ ] **Step 1: Replace the whole file**

Current full content:

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
    audio.play().catch(() => {});
    playingUrl.value = url;
  }

  return { playingUrl, toggle };
}
```

Replace with:

```js
import { ref } from "vue";

const audio = new Audio();
const playingUrl = ref(null);
const currentTime = ref(0);
const duration = ref(0);

audio.addEventListener("ended", () => {
  playingUrl.value = null;
});
audio.addEventListener("timeupdate", () => {
  currentTime.value = audio.currentTime;
});
audio.addEventListener("loadedmetadata", () => {
  duration.value = audio.duration;
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
    currentTime.value = 0;
    audio.play().catch(() => {});
    playingUrl.value = url;
  }

  function stop() {
    audio.pause();
    playingUrl.value = null;
  }

  return { playingUrl, currentTime, duration, toggle, stop };
}
```

This is backwards-compatible: `playingUrl`/`toggle` keep the same
signature, so nothing else needs to change yet.

- [ ] **Step 2: Verify**

Run: `cd spotify_explorer/frontend && npx vite build --logLevel warn`
Expected: build succeeds.

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/composables/usePreviewPlayer.js
git commit -m "feat(spotify-explorer): expose real progress and stop() from usePreviewPlayer"
```

---

### Task 4: New `useNowPlaying.js` composable

**Files:**
- Create: `composables/useNowPlaying.js`

- [ ] **Step 1: Create the file**

```js
import { ref } from "vue";

const current = ref(null); // { image, title, subtitle, url, previewUrl, durationMs } | null

export function useNowPlaying() {
  function open(track) {
    current.value = track;
  }

  function close() {
    current.value = null;
  }

  return { current, open, close };
}
```

- [ ] **Step 2: Verify**

Run: `cd spotify_explorer/frontend && npx vite build --logLevel warn`
Expected: build succeeds (file isn't imported anywhere yet, so this just confirms valid JS).

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/composables/useNowPlaying.js
git commit -m "feat(spotify-explorer): add useNowPlaying composable"
```

---

### Task 5: Strip `MediaItemRow.vue` down to image + info

**Files:**
- Modify: `components/MediaItemRow.vue` (whole file)

- [ ] **Step 1: Replace the whole file**

Current full content:

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

Replace with:

```vue
<script setup>
defineProps({
  image: { type: String, default: null },
  title: { type: String, required: true },
  subtitle: { type: String, default: "" },
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
  </div>
</template>
```

Note: this temporarily breaks every caller that still passes
`:url="..."` / `:preview-url="..."` (Vue just ignores unknown props —
build won't fail, but the play/link icons vanish everywhere until
Tasks 7-14 wrap the track rows in the new clickable button). That's
expected mid-plan state.

- [ ] **Step 2: Verify**

Run: `cd spotify_explorer/frontend && npx vite build --logLevel warn`
Expected: build succeeds.

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/components/MediaItemRow.vue
git commit -m "refactor(spotify-explorer): strip inline preview/link buttons from MediaItemRow"
```

---

### Task 6: Add `now-playing-*` styles

**Files:**
- Modify: `style.css:492` (append at end of file)

- [ ] **Step 1: Append the new block**

The file currently ends with:

```css
.preview-spotify-link:hover {
  text-decoration: underline;
}
```

Append after that (new blank line, then the block below):

```css

/* Now-playing modal (click on a track row) */
.now-playing-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.now-playing-modal {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: 2rem;
  width: 320px;
  max-width: 90vw;
  text-align: center;
  position: relative;
}

.now-playing-close {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
}

.now-playing-art {
  width: 100%;
  aspect-ratio: 1;
  border-radius: var(--radius-sm);
  object-fit: cover;
  background: var(--bg-elevated-hover);
}

.now-playing-equalizer {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  gap: 4px;
  height: 20px;
  margin: 1rem 0;
}

.now-playing-equalizer span {
  width: 4px;
  height: 6px;
  background: var(--accent);
  border-radius: 2px;
}

.now-playing-equalizer.is-playing span {
  animation: now-playing-bounce 0.8s ease-in-out infinite;
}

.now-playing-equalizer span:nth-child(2) { animation-delay: 0.15s; }
.now-playing-equalizer span:nth-child(3) { animation-delay: 0.3s; }
.now-playing-equalizer span:nth-child(4) { animation-delay: 0.45s; }

@keyframes now-playing-bounce {
  0%, 100% { height: 6px; }
  50% { height: 20px; }
}

.now-playing-title {
  margin: 0.25rem 0 0;
}

.now-playing-subtitle {
  color: var(--text-secondary);
  margin: 0.25rem 0 1rem;
}

.now-playing-progress-track {
  height: 4px;
  background: var(--bg-elevated-hover);
  border-radius: 2px;
  overflow: hidden;
}

.now-playing-progress-fill {
  height: 100%;
  background: var(--accent);
}

.now-playing-hint {
  color: var(--text-muted);
  font-size: 0.8rem;
  margin: 0.5rem 0 1rem;
}

.now-playing-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.now-playing-play-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--accent);
  color: #000;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.now-playing-play-btn:hover {
  background: var(--accent-hover);
}
```

- [ ] **Step 2: Verify**

Run: `cd spotify_explorer/frontend && npx vite build --logLevel warn`
Expected: build succeeds.

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/style.css
git commit -m "feat(spotify-explorer): add now-playing modal styles"
```

---

### Task 7: New `NowPlayingModal.vue`

**Files:**
- Create: `components/NowPlayingModal.vue`

- [ ] **Step 1: Create the file**

```vue
<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useNowPlaying } from "../composables/useNowPlaying.js";
import { usePreviewPlayer } from "../composables/usePreviewPlayer.js";
import Icon from "./Icon.vue";

const { current, close } = useNowPlaying();
const { playingUrl, currentTime, duration, toggle, stop } = usePreviewPlayer();

const hasPreview = computed(() => Boolean(current.value?.previewUrl));
const isPlaying = computed(() => hasPreview.value && playingUrl.value === current.value.previewUrl);

const fakeElapsedMs = ref(0);
let fakeTimer = null;

function startFakeProgress() {
  const totalMs = current.value?.durationMs || 30000;
  fakeTimer = setInterval(() => {
    fakeElapsedMs.value = (fakeElapsedMs.value + 250) % totalMs;
  }, 250);
}

function stopFakeProgress() {
  clearInterval(fakeTimer);
  fakeTimer = null;
  fakeElapsedMs.value = 0;
}

watch(current, (track, previous) => {
  if (previous) stopFakeProgress();
  if (!track) return;
  if (track.previewUrl) {
    toggle(track.previewUrl);
  } else {
    startFakeProgress();
  }
});

function handleClose() {
  stop();
  stopFakeProgress();
  close();
}

function handleKeydown(event) {
  if (event.key === "Escape") handleClose();
}

onMounted(() => window.addEventListener("keydown", handleKeydown));
onUnmounted(() => window.removeEventListener("keydown", handleKeydown));

const progressPercent = computed(() => {
  if (!current.value) return 0;
  if (hasPreview.value) {
    return duration.value ? (currentTime.value / duration.value) * 100 : 0;
  }
  const totalMs = current.value.durationMs || 30000;
  return (fakeElapsedMs.value / totalMs) * 100;
});

function formatSeconds(seconds) {
  if (!seconds || Number.isNaN(seconds)) return "0:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}
</script>

<template>
  <div v-if="current" class="now-playing-backdrop" @click.self="handleClose">
    <div class="now-playing-modal">
      <button type="button" class="now-playing-close" aria-label="Fechar" @click="handleClose">
        <Icon name="close" :size="20" />
      </button>

      <img v-if="current.image" :src="current.image" :alt="current.title" class="now-playing-art">
      <div v-else class="now-playing-art"></div>

      <div class="now-playing-equalizer" :class="{ 'is-playing': isPlaying || !hasPreview }">
        <span v-for="n in 4" :key="n"></span>
      </div>

      <h3 class="now-playing-title">{{ current.title }}</h3>
      <p v-if="current.subtitle" class="now-playing-subtitle">{{ current.subtitle }}</p>

      <div class="now-playing-progress-track">
        <div class="now-playing-progress-fill" :style="{ width: `${progressPercent}%` }"></div>
      </div>
      <p v-if="!hasPreview" class="now-playing-hint">
        Prévia indisponível — visualização ilustrativa (restrição da Spotify desde nov/2024)
      </p>
      <p v-else class="now-playing-hint">
        {{ formatSeconds(currentTime) }} / {{ formatSeconds(duration) }}
      </p>

      <div class="now-playing-controls">
        <button
          v-if="hasPreview"
          type="button"
          class="now-playing-play-btn"
          :aria-label="isPlaying ? 'Pausar' : 'Tocar'"
          @click="toggle(current.previewUrl)"
        >
          <Icon :name="isPlaying ? 'pause' : 'player'" :size="24" />
        </button>
        <a v-if="current.url" :href="current.url" target="_blank" rel="noopener" class="btn btn-secondary">
          <Icon name="external-link" :size="16" />
          Abrir no Spotify
        </a>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Verify**

Run: `cd spotify_explorer/frontend && npx vite build --logLevel warn`
Expected: build succeeds (not mounted anywhere yet — Task 8 does that).

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/components/NowPlayingModal.vue
git commit -m "feat(spotify-explorer): add NowPlayingModal component"
```

---

### Task 8: Mount the modal in `App.vue`

**Files:**
- Modify: `App.vue:1-17` (imports), `App.vue:52-70` (template)

- [ ] **Step 1: Import the component**

Current top of `<script setup>`:

```js
import { onMounted, reactive, ref, watch } from "vue";
import { fetchJSON } from "./composables/useApi.js";
import { useAuthStatus } from "./composables/useAuthStatus.js";
import { useTabNavigation } from "./composables/useTabNavigation.js";
import AppSidebar from "./components/AppSidebar.vue";
```

Add right after the `AppSidebar` import:

```js
import { onMounted, reactive, ref, watch } from "vue";
import { fetchJSON } from "./composables/useApi.js";
import { useAuthStatus } from "./composables/useAuthStatus.js";
import { useTabNavigation } from "./composables/useTabNavigation.js";
import AppSidebar from "./components/AppSidebar.vue";
import NowPlayingModal from "./components/NowPlayingModal.vue";
```

- [ ] **Step 2: Mount it in the template**

Current template end:

```vue
      <KeepAlive>
        <component :is="tabs.find((t) => t.id === activeTab).component" />
      </KeepAlive>
    </main>
  </div>
</template>
```

Change to:

```vue
      <KeepAlive>
        <component :is="tabs.find((t) => t.id === activeTab).component" />
      </KeepAlive>
    </main>

    <NowPlayingModal />
  </div>
</template>
```

(`<NowPlayingModal />` is a sibling of `<main>`, both inside `.app-shell` — outside the `KeepAlive`/tab switching so it can never be torn down mid-"playback".)

- [ ] **Step 3: Verify**

Run: `cd spotify_explorer/frontend && npx vite build --logLevel warn`
Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
git add spotify_explorer/frontend/src/App.vue
git commit -m "feat(spotify-explorer): mount NowPlayingModal in App"
```

---

### Task 9: Wire up `SearchTab.vue` (conditional: only `track` results)

**Files:**
- Modify: `tabs/SearchTab.vue:1-8` (imports/setup), `tabs/SearchTab.vue:61-65` (template)

- [ ] **Step 1: Import `useNowPlaying`**

Current imports:

```js
import { computed, reactive, ref } from "vue";
import { useApi } from "../composables/useApi.js";
import { useHistory } from "../composables/useHistory.js";
import { trackSummary, artistSummary, albumSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import MediaItemRow from "../components/MediaItemRow.vue";
```

Add the import and call the composable:

```js
import { computed, reactive, ref } from "vue";
import { useApi } from "../composables/useApi.js";
import { useHistory } from "../composables/useHistory.js";
import { useNowPlaying } from "../composables/useNowPlaying.js";
import { trackSummary, artistSummary, albumSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const { open } = useNowPlaying();
```

Place the `const { open } = useNowPlaying();` line right after the existing `const { items: history, add: addToHistory } = useHistory("search");` line.

- [ ] **Step 2: Wrap track rows in the template**

Current:

```vue
      <template #preview>
        <div v-for="(item, i) in items" :key="i">
          <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" :preview-url="item.previewUrl" />
        </div>
      </template>
```

Change to:

```vue
      <template #preview>
        <div v-for="(item, i) in items" :key="i">
          <button v-if="submittedType === 'track'" type="button" class="media-item-clickable" @click="open(item)">
            <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" />
          </button>
          <MediaItemRow v-else :image="item.image" :title="item.title" :subtitle="item.subtitle" />
        </div>
      </template>
```

- [ ] **Step 3: Verify**

Run: `cd spotify_explorer/frontend && npx vite build --logLevel warn`
Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/SearchTab.vue
git commit -m "feat(spotify-explorer): open now-playing modal from Search track results"
```

---

### Task 10: Wire up `RecommendationsTab.vue` (always tracks)

**Files:**
- Modify: `tabs/RecommendationsTab.vue:1-7` (imports/setup), `tabs/RecommendationsTab.vue:58-62` (template)

- [ ] **Step 1: Import and call `useNowPlaying`**

Current imports:

```js
import { computed, reactive } from "vue";
import { useApi } from "../composables/useApi.js";
import { useHistory } from "../composables/useHistory.js";
import { trackSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import MediaItemRow from "../components/MediaItemRow.vue";
```

Change to:

```js
import { computed, reactive } from "vue";
import { useApi } from "../composables/useApi.js";
import { useHistory } from "../composables/useHistory.js";
import { useNowPlaying } from "../composables/useNowPlaying.js";
import { trackSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const { open } = useNowPlaying();
```

Place `const { open } = useNowPlaying();` right after `const { items: history, add: addToHistory } = useHistory("recommendations");`.

- [ ] **Step 2: Wrap the rows**

Current:

```vue
      <template #preview>
        <div v-for="(item, i) in items" :key="i">
          <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" :preview-url="item.previewUrl" />
        </div>
      </template>
```

Change to:

```vue
      <template #preview>
        <div v-for="(item, i) in items" :key="i">
          <button type="button" class="media-item-clickable" @click="open(item)">
            <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" />
          </button>
        </div>
      </template>
```

- [ ] **Step 3: Verify**

Run: `cd spotify_explorer/frontend && npx vite build --logLevel warn`
Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/RecommendationsTab.vue
git commit -m "feat(spotify-explorer): open now-playing modal from Recommendations"
```

---

### Task 11: Wire up `ArtistTab.vue` (top tracks only, not related artists)

**Files:**
- Modify: `tabs/ArtistTab.vue:1-9` (imports/setup), `tabs/ArtistTab.vue:78-83` (template)

- [ ] **Step 1: Import and call `useNowPlaying`**

Current imports:

```js
import { computed, reactive, ref } from "vue";
import { fetchJSON } from "../composables/useApi.js";
import { useHistory } from "../composables/useHistory.js";
import { useNavigationTarget } from "../composables/useTabNavigation.js";
import { trackSummary, artistSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import ArtistPreview from "../components/previews/ArtistPreview.vue";
import MediaItemRow from "../components/MediaItemRow.vue";
```

Change to:

```js
import { computed, reactive, ref } from "vue";
import { fetchJSON } from "../composables/useApi.js";
import { useHistory } from "../composables/useHistory.js";
import { useNavigationTarget } from "../composables/useTabNavigation.js";
import { useNowPlaying } from "../composables/useNowPlaying.js";
import { trackSummary, artistSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import ArtistPreview from "../components/previews/ArtistPreview.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const { open } = useNowPlaying();
```

Place `const { open } = useNowPlaying();` right after `const { items: history, add: addToHistory } = useHistory("artist");`.

- [ ] **Step 2: Wrap only the top-tracks rows**

Current (the top-tracks block only — related-artists block below it is untouched):

```vue
        <div v-if="topTracksItems.length">
          <h3>Top tracks</h3>
          <div v-for="(item, i) in topTracksItems" :key="i">
            <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" :preview-url="item.previewUrl" />
          </div>
        </div>
```

Change to:

```vue
        <div v-if="topTracksItems.length">
          <h3>Top tracks</h3>
          <div v-for="(item, i) in topTracksItems" :key="i">
            <button type="button" class="media-item-clickable" @click="open(item)">
              <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" />
            </button>
          </div>
        </div>
```

The `relatedArtistsItems` block right below stays exactly as-is (still
passes `:url="item.url"` to `MediaItemRow`, which now silently ignores
that prop per Task 5 — no visible external-link icon there anymore,
matching the spec's decision that only track rows keep any click
affordance).

- [ ] **Step 3: Verify**

Run: `cd spotify_explorer/frontend && npx vite build --logLevel warn`
Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/ArtistTab.vue
git commit -m "feat(spotify-explorer): open now-playing modal from Artist top tracks"
```

---

### Task 12: Wire up `AlbumTab.vue` (always tracks)

**Files:**
- Modify: `tabs/AlbumTab.vue:1-8` (imports/setup), `tabs/AlbumTab.vue:43-48` (template)

- [ ] **Step 1: Import and call `useNowPlaying`**

Current imports:

```js
import { computed, reactive, ref } from "vue";
import { useApi } from "../composables/useApi.js";
import { useHistory } from "../composables/useHistory.js";
import { trackSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import AlbumPreview from "../components/previews/AlbumPreview.vue";
import MediaItemRow from "../components/MediaItemRow.vue";
```

Change to:

```js
import { computed, reactive, ref } from "vue";
import { useApi } from "../composables/useApi.js";
import { useHistory } from "../composables/useHistory.js";
import { useNowPlaying } from "../composables/useNowPlaying.js";
import { trackSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import AlbumPreview from "../components/previews/AlbumPreview.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const { open } = useNowPlaying();
```

Place `const { open } = useNowPlaying();` right after `const { items: history, add: addToHistory } = useHistory("album");`.

- [ ] **Step 2: Wrap the rows**

Current:

```vue
        <div v-if="tracks.length">
          <h3>Faixas</h3>
          <div v-for="(item, i) in tracks" :key="i">
            <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" :preview-url="item.previewUrl" />
          </div>
        </div>
```

Change to:

```vue
        <div v-if="tracks.length">
          <h3>Faixas</h3>
          <div v-for="(item, i) in tracks" :key="i">
            <button type="button" class="media-item-clickable" @click="open(item)">
              <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" />
            </button>
          </div>
        </div>
```

- [ ] **Step 3: Verify**

Run: `cd spotify_explorer/frontend && npx vite build --logLevel warn`
Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/AlbumTab.vue
git commit -m "feat(spotify-explorer): open now-playing modal from Album tracks"
```

---

### Task 13: Wire up `PlaylistTab.vue` (always tracks, when available)

**Files:**
- Modify: `tabs/PlaylistTab.vue:1-9` (imports/setup), `tabs/PlaylistTab.vue:62-67` (template)

- [ ] **Step 1: Import and call `useNowPlaying`**

Current imports:

```js
import { computed, reactive, ref } from "vue";
import { useApi } from "../composables/useApi.js";
import { useHistory } from "../composables/useHistory.js";
import { useNavigationTarget } from "../composables/useTabNavigation.js";
import { trackSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import PlaylistPreview from "../components/previews/PlaylistPreview.vue";
import MediaItemRow from "../components/MediaItemRow.vue";
```

Change to:

```js
import { computed, reactive, ref } from "vue";
import { useApi } from "../composables/useApi.js";
import { useHistory } from "../composables/useHistory.js";
import { useNavigationTarget } from "../composables/useTabNavigation.js";
import { useNowPlaying } from "../composables/useNowPlaying.js";
import { trackSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import PlaylistPreview from "../components/previews/PlaylistPreview.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const { open } = useNowPlaying();
```

Place `const { open } = useNowPlaying();` right after `const { items: history, add: addToHistory } = useHistory("playlist");`.

- [ ] **Step 2: Wrap the rows**

Current:

```vue
        <div v-if="tracks.length">
          <h3>Faixas</h3>
          <div v-for="(item, i) in tracks" :key="i">
            <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" :preview-url="item.previewUrl" />
          </div>
        </div>
```

Change to:

```vue
        <div v-if="tracks.length">
          <h3>Faixas</h3>
          <div v-for="(item, i) in tracks" :key="i">
            <button type="button" class="media-item-clickable" @click="open(item)">
              <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" />
            </button>
          </div>
        </div>
```

- [ ] **Step 3: Verify**

Run: `cd spotify_explorer/frontend && npx vite build --logLevel warn`
Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/PlaylistTab.vue
git commit -m "feat(spotify-explorer): open now-playing modal from Playlist tracks"
```

---

### Task 14: Wire up `MeusDadosTab.vue` (3 lists: top items, curtidas, recentes)

**Files:**
- Modify: `tabs/MeusDadosTab.vue:1-7` (imports/setup), `tabs/MeusDadosTab.vue:82-117` (template)

- [ ] **Step 1: Import and call `useNowPlaying`**

Current imports:

```js
import { computed, reactive } from "vue";
import { useApi } from "../composables/useApi.js";
import { useAuthStatus } from "../composables/useAuthStatus.js";
import { trackSummary, artistSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import MediaItemRow from "../components/MediaItemRow.vue";
```

Change to:

```js
import { computed, reactive } from "vue";
import { useApi } from "../composables/useApi.js";
import { useAuthStatus } from "../composables/useAuthStatus.js";
import { useNowPlaying } from "../composables/useNowPlaying.js";
import { trackSummary, artistSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const { open } = useNowPlaying();
```

Place `const { open } = useNowPlaying();` right after `const { state: authState } = useAuthStatus();`.

- [ ] **Step 2: Wrap the top-items row (conditional: only when `topTarget` is `tracks`)**

Current:

```vue
        <ResultPanel :status="top.status" :data="topResult.data" empty-hint="Clique em Top tracks ou Top artists">
          <template #preview>
            <div v-for="(item, i) in topItems" :key="i">
              <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" :preview-url="item.previewUrl" />
            </div>
          </template>
        </ResultPanel>
```

Change to:

```vue
        <ResultPanel :status="top.status" :data="topResult.data" empty-hint="Clique em Top tracks ou Top artists">
          <template #preview>
            <div v-for="(item, i) in topItems" :key="i">
              <button v-if="topTarget === 'tracks'" type="button" class="media-item-clickable" @click="open(item)">
                <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" />
              </button>
              <MediaItemRow v-else :image="item.image" :title="item.title" :subtitle="item.subtitle" />
            </div>
          </template>
        </ResultPanel>
```

- [ ] **Step 3: Wrap the "faixas curtidas" row (always tracks)**

Current:

```vue
        <ResultPanel :status="saved.status" :data="savedResult.data" empty-hint="Clique em Buscar curtidas">
          <template #preview>
            <div v-for="(item, i) in savedItems" :key="i">
              <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" :preview-url="item.previewUrl" />
            </div>
          </template>
        </ResultPanel>
```

Change to:

```vue
        <ResultPanel :status="saved.status" :data="savedResult.data" empty-hint="Clique em Buscar curtidas">
          <template #preview>
            <div v-for="(item, i) in savedItems" :key="i">
              <button type="button" class="media-item-clickable" @click="open(item)">
                <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" />
              </button>
            </div>
          </template>
        </ResultPanel>
```

- [ ] **Step 4: Wrap the "tocadas recentemente" row (always tracks)**

Current:

```vue
        <ResultPanel
          :status="recentlyPlayed.status"
          :data="recentlyPlayedResult.data"
          empty-hint="Clique em Buscar recentes"
        >
          <template #preview>
            <div v-for="(item, i) in recentlyPlayedItems" :key="i">
              <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" :preview-url="item.previewUrl" />
            </div>
          </template>
        </ResultPanel>
```

Change to:

```vue
        <ResultPanel
          :status="recentlyPlayed.status"
          :data="recentlyPlayedResult.data"
          empty-hint="Clique em Buscar recentes"
        >
          <template #preview>
            <div v-for="(item, i) in recentlyPlayedItems" :key="i">
              <button type="button" class="media-item-clickable" @click="open(item)">
                <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" />
              </button>
            </div>
          </template>
        </ResultPanel>
```

- [ ] **Step 5: Verify**

Run: `cd spotify_explorer/frontend && npx vite build --logLevel warn`
Expected: build succeeds.

- [ ] **Step 6: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/MeusDadosTab.vue
git commit -m "feat(spotify-explorer): open now-playing modal from Meus Dados track lists"
```

---

### Task 15: Wire up `PlayerTab.vue` (queue, always tracks)

**Files:**
- Modify: `tabs/PlayerTab.vue:1-8` (imports/setup), `tabs/PlayerTab.vue:182-187` (template)

- [ ] **Step 1: Import and call `useNowPlaying`**

Current imports:

```js
import { computed, reactive } from "vue";
import { fetchJSON } from "../composables/useApi.js";
import { useAuthStatus } from "../composables/useAuthStatus.js";
import { trackSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import TrackPreview from "../components/previews/TrackPreview.vue";
import MediaItemRow from "../components/MediaItemRow.vue";
```

Change to:

```js
import { computed, reactive } from "vue";
import { fetchJSON } from "../composables/useApi.js";
import { useAuthStatus } from "../composables/useAuthStatus.js";
import { useNowPlaying } from "../composables/useNowPlaying.js";
import { trackSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import TrackPreview from "../components/previews/TrackPreview.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const { open } = useNowPlaying();
```

Place `const { open } = useNowPlaying();` right after `const { state: authState } = useAuthStatus();`.

- [ ] **Step 2: Wrap the queue rows**

Current:

```vue
          <div v-if="queueItems.length">
            <h3>Fila</h3>
            <div v-for="(item, i) in queueItems" :key="i">
              <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" :preview-url="item.previewUrl" />
            </div>
          </div>
```

Change to:

```vue
          <div v-if="queueItems.length">
            <h3>Fila</h3>
            <div v-for="(item, i) in queueItems" :key="i">
              <button type="button" class="media-item-clickable" @click="open(item)">
                <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" />
              </button>
            </div>
          </div>
```

- [ ] **Step 3: Verify**

Run: `cd spotify_explorer/frontend && npx vite build --logLevel warn`
Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/PlayerTab.vue
git commit -m "feat(spotify-explorer): open now-playing modal from Player queue"
```

---

### Task 16: Full build + manual browser verification

**Files:** none (verification only)

- [ ] **Step 1: Production build**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: exit code 0, `../static/frontend` regenerated with no warnings about unused/unknown props beyond Vue's normal attribute-fallthrough behavior.

- [ ] **Step 2: Start backend + dev frontend**

```bash
cd spotify_explorer && python app.py &
cd spotify_explorer/frontend && npm run dev
```

Open `http://127.0.0.1:5173`.

- [ ] **Step 3: Verify Search tab**

Search for any track (e.g. query `test`, type `track`). Click a result
row. Expected: `NowPlayingModal` opens over the page, showing album art
(or empty placeholder), title/artist, equalizer animation running,
progress bar moving, "Abrir no Spotify" link present. If the track has
no `preview_url` (expected — see spec's known restriction), there's no
play/pause button and the "Prévia indisponível" hint shows instead of
a timer.

- [ ] **Step 4: Verify close behaviors**

With the modal open: click the X button (closes), reopen, click the
dark backdrop outside the card (closes), reopen, press `Escape`
(closes). All three must close the modal and stop any audio/fake
progress (re-opening should always restart from 0%, not resume a
stale progress value).

- [ ] **Step 5: Verify the row itself is clean**

In Search results, confirm the track row no longer shows the small
inline play icon or the external-link icon — just image + title +
subtitle, and the whole row is clickable (cursor pointer, hover
background from the existing `.media-item-row:hover` style).

- [ ] **Step 6: Spot-check two more surfaces**

Pick two of: Album (paste a real album ID), Artist (top tracks
section only), Meus Dados (curtidas/recentes/top tracks — needs
Spotify login), Player queue (needs login + active playback). Confirm
clicking a track row opens the same modal. Confirm Artist's
"Related artists" rows and Search's artist/album results do **not**
open the modal (no click affordance at all now, since `MediaItemRow`
lost its icons — this is expected per the spec's scope).

- [ ] **Step 7: No commit needed**

This task is verification-only; if any check fails, fix the relevant
earlier task's file and re-commit there (`git commit --fixup` or a new
small commit), then re-run this task's checks.

---

## Self-Review Notes

- **Spec coverage:** every section of the spec (`useNowPlaying`,
  `usePreviewPlayer` extension, `NowPlayingModal`, `close` icon,
  `MediaItemRow` stripped, `trackSummary` `durationMs`, all 8
  track-bearing call sites, `App.vue` mount, styles, manual
  verification) has a corresponding task above (Tasks 1-16).
- **Placeholder scan:** no TBD/TODO; every step shows the literal
  before/after code.
- **Type consistency:** `open(track)` is called the same way in every
  tab (`open(item)`, where `item` is always the object returned by
  `trackSummary()` — same shape `useNowPlaying.js` and
  `NowPlayingModal.vue` expect: `image`, `title`, `subtitle`, `url`,
  `previewUrl`, `durationMs`). `usePreviewPlayer`'s `toggle`/`stop`
  signatures are unchanged from the pre-existing preview feature, so
  no caller outside `NowPlayingModal.vue` needed updating.
</content>
