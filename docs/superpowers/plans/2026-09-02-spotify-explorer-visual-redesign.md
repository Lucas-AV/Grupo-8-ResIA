# Spotify Explorer Visual/UX Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign `spotify_explorer`'s Vue frontend with a Spotify-branded dark theme, sidebar navigation, rich previews of known Spotify object shapes (track/artist/album cards), and real usability upgrades (copy-to-clipboard, search history, loading skeletons, empty states) — with zero new npm dependencies and zero backend changes.

**Architecture:** New shared presentational components (`Icon`, `SkeletonBlock`, `EmptyState`, `MediaItemRow`, `ResultPanel`) and two small preview components (`TrackPreview`, `ArtistPreview`) sit between the existing `useApi`/`fetchJSON` composables and the 5 tab components, which get rewritten to use them. A new `AppSidebar.vue` replaces the top tab-nav in `App.vue`. A new `spotifyShapes.js` util safely extracts `{image, title, subtitle}` from raw Spotify API objects for the preview components, falling back to nothing (just the raw JSON) when a shape doesn't match — so the redesign never hides what the API actually returned, it just organizes it better.

**Tech Stack:** Vue 3 (Composition API, `<script setup>`), pure CSS (no component library), inline SVG icons (no icon library), `localStorage` for history (no state library). No changes to `package.json`.

**Spec:** `docs/superpowers/specs/2026-09-02-spotify-explorer-visual-redesign.md`

**Verification convention (every task):** this project has no JS test framework (established, deliberate choice across all prior frontend work) — verification is `cd spotify_explorer/frontend && npm run build` succeeding (Vite's Vue compiler catches template/syntax errors) plus `cd spotify_explorer && pytest -v` (55 tests) confirming the frontend-only changes never touch backend behavior. A full visual/browser check requires a human and is the final task's job.

---

## Task 1: Design tokens and base styles

**Files:**
- Modify: `spotify_explorer/frontend/src/style.css`

Purely additive — nothing existing is deleted yet (later tasks replace the markup that uses the old classes; a final cleanup task removes what's left unused). One exception: the existing `body` rule's `max-width`/`padding`/`margin-inline` must be reset here, otherwise the new full-width sidebar layout (Task 6) would render squeezed into the old 960px centered column.

- [ ] **Step 1: Append the new tokens, layout, and component styles**

Add this entire block to the END of `spotify_explorer/frontend/src/style.css` (after the existing rules — don't remove or reorder anything already there):

```css
/* --- Spotify-branded redesign: tokens, shell layout, new components --- */

:root {
  --bg-base: #121212;
  --bg-sidebar: #000000;
  --bg-elevated: #181818;
  --bg-elevated-hover: #282828;
  --accent: #1db954;
  --accent-hover: #1ed760;
  --text-primary: #ffffff;
  --text-secondary: #b3b3b3;
  --text-muted: #6a6a6a;
  --border-subtle: rgba(255, 255, 255, 0.1);
  --radius-sm: 4px;
  --radius-md: 8px;
  --sidebar-width: 240px;
}

/* Reset the old centered-column body rule for the new full-width shell */
body {
  margin: 0;
  padding: 0;
  max-width: none;
  background: var(--bg-base);
  color: var(--text-primary);
}

h2 {
  margin: 0 0 1rem;
  font-size: 1.5rem;
  font-weight: 800;
}

h3 {
  margin: 1rem 0 0.5rem;
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-secondary);
}

/* App shell: sidebar + main content */
.app-shell {
  display: flex;
  min-height: 100vh;
}

.app-sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  background: var(--bg-sidebar);
  padding: 1.5rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.app-sidebar-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--text-primary);
}

.app-sidebar-subtitle {
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.sidebar-nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  border-radius: var(--radius-sm);
  border: none;
  border-left: 3px solid transparent;
  background: none;
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  text-align: left;
}

.sidebar-nav-item:hover {
  color: var(--text-primary);
  background: var(--bg-elevated);
}

.sidebar-nav-item.active {
  color: var(--text-primary);
  background: var(--bg-elevated);
  border-left-color: var(--accent);
}

.sidebar-footer {
  margin-top: auto;
  padding-top: 1rem;
  border-top: 1px solid var(--border-subtle);
  font-size: 0.85rem;
}

.sidebar-user {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.app-main {
  flex: 1;
  min-width: 0;
  padding: 2rem;
  max-width: 960px;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 1.2rem;
  border-radius: 999px;
  border: none;
  background: var(--accent);
  color: #000000;
  font-weight: 700;
  font-size: 0.85rem;
  cursor: pointer;
  text-decoration: none;
}

.btn:hover {
  background: var(--accent-hover);
}

.btn-secondary {
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.btn-secondary:hover {
  background: var(--bg-elevated-hover);
}

/* History chips */
.history-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.history-chip {
  padding: 0.3rem 0.75rem;
  border-radius: 999px;
  background: var(--bg-elevated);
  color: var(--text-secondary);
  font-size: 0.8rem;
  border: 1px solid var(--border-subtle);
  cursor: pointer;
}

.history-chip:hover {
  color: var(--text-primary);
  border-color: var(--accent);
}

/* Media item row (reusable track/artist/album list row) */
.media-item-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  border-radius: var(--radius-sm);
}

.media-item-row:hover {
  background: var(--bg-elevated);
}

.media-item-image {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-sm);
  object-fit: cover;
  background: var(--bg-elevated-hover);
  flex-shrink: 0;
}

.media-item-title {
  font-weight: 700;
  color: var(--text-primary);
  font-size: 0.9rem;
}

.media-item-subtitle {
  color: var(--text-secondary);
  font-size: 0.8rem;
}

/* Preview "hero" cards (Track & Audio, Artist tabs) */
.preview-card {
  display: flex;
  gap: 1.5rem;
  padding: 1.5rem;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  margin-bottom: 1.5rem;
}

.preview-image {
  width: 150px;
  height: 150px;
  border-radius: var(--radius-sm);
  object-fit: cover;
  background: var(--bg-elevated-hover);
  flex-shrink: 0;
}

.preview-title {
  font-size: 1.4rem;
  font-weight: 800;
  color: var(--text-primary);
}

.preview-subtitle {
  color: var(--text-secondary);
  margin-top: 0.25rem;
}

.preview-genres {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.75rem;
}

.preview-genre-chip {
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  background: var(--bg-elevated-hover);
  color: var(--text-secondary);
  font-size: 0.75rem;
}

.audio-feature-bar {
  display: grid;
  grid-template-columns: 100px 1fr 3rem;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.audio-feature-track {
  height: 6px;
  border-radius: 3px;
  background: var(--bg-elevated-hover);
  overflow: hidden;
}

.audio-feature-fill {
  height: 100%;
  background: var(--accent);
}

/* Skeleton loading state */
.skeleton-block {
  height: 1rem;
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, var(--bg-elevated) 25%, var(--bg-elevated-hover) 50%, var(--bg-elevated) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.4s ease-in-out infinite;
  margin-bottom: 0.6rem;
}

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Empty state */
.empty-state {
  padding: 2rem;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.9rem;
}

/* Result panel chrome */
.result-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 1rem 0 0.5rem;
}

/* JSON value type colors (JsonViewer.vue) */
.json-string { color: #79c0ff; }
.json-number { color: #d2a8ff; }
.json-boolean { color: var(--accent); }
.json-null { color: var(--text-muted); }
```

- [ ] **Step 2: Verify**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: builds without errors (no markup changed yet, so the app still looks like the old vanilla-parity version, just on a dark background now — that's expected and temporary; later tasks bring the markup in line with these new styles).

Run: `cd spotify_explorer && pytest -v`
Expected: all 55 tests pass (frontend-only change).

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/style.css
git commit -m "feat: add Spotify-branded design tokens and component styles"
```

---

## Task 2: Small presentational components — `Icon`, `SkeletonBlock`, `EmptyState`, `MediaItemRow`

**Files:**
- Create: `spotify_explorer/frontend/src/components/Icon.vue`
- Create: `spotify_explorer/frontend/src/components/SkeletonBlock.vue`
- Create: `spotify_explorer/frontend/src/components/EmptyState.vue`
- Create: `spotify_explorer/frontend/src/components/MediaItemRow.vue`

Four small, dependency-free "dumb" components — no business logic, just props in, markup out. None of these are wired into the app yet (that happens in Tasks 5-10) — this task just creates them so later tasks can import them.

- [ ] **Step 1: Create `Icon.vue`**

A tiny inline-SVG icon registry — no icon library, no network request. Covers every icon this redesign needs: `search` (Search tab), `disc` (Track & Audio tab), `mic` (Artist tab), `sparkles` (Recommendations tab), `heart` (Meus dados tab), `waveform` (sidebar header mark), `copy`/`check` (copy-to-clipboard button), `logout` (sidebar footer).

```vue
<script setup>
const props = defineProps({
  name: { type: String, required: true },
  size: { type: Number, default: 20 },
});

const paths = {
  search: "M9 3a6 6 0 104.472 10.032l3.248 3.248a1 1 0 001.414-1.414l-3.248-3.248A6 6 0 009 3zm-4 6a4 4 0 118 0 4 4 0 01-8 0z",
  disc: "M10 2a8 8 0 100 16 8 8 0 000-16zm0 5a3 3 0 110 6 3 3 0 010-6z",
  mic: "M10 2a3 3 0 00-3 3v5a3 3 0 006 0V5a3 3 0 00-3-3zM5 10a1 1 0 10-2 0 7 7 0 006 6.92V19a1 1 0 102 0v-2.08A7 7 0 0017 10a1 1 0 10-2 0 5 5 0 01-10 0z",
  sparkles: "M6 2l1 3 3 1-3 1-1 3-1-3-3-1 3-1 1-3zM15 9l1.5 4 4 1.5-4 1.5-1.5 4-1.5-4-4-1.5 4-1.5 1.5-4z",
  heart: "M10 17.5l-1.1-1C4.4 12.9 2 10.6 2 7.8 2 5.6 3.7 4 5.9 4c1.2 0 2.4.6 3.1 1.5A4 4 0 0112.1 4c2.2 0 3.9 1.6 3.9 3.8 0 2.8-2.4 5.1-6.9 8.7l-1.1 1z",
  waveform: "M3 10h2v4H3v-4zm4-4h2v12H7V6zm4 2h2v8h-2V8zm4-5h2v18h-2V3z",
  copy: "M8 2a2 2 0 00-2 2v8a2 2 0 002 2h6a2 2 0 002-2V6.83a2 2 0 00-.59-1.41l-2.83-2.83A2 2 0 0011.17 2H8zm0 2h3v3a1 1 0 001 1h3v6H8V4zM4 6a2 2 0 00-2 2v8a2 2 0 002 2h6a2 2 0 002-2h-2v0H4V8h2V6H4z",
  check: "M16.7 5.3a1 1 0 010 1.4l-8 8a1 1 0 01-1.4 0l-4-4a1 1 0 111.4-1.4L8 12.6l7.3-7.3a1 1 0 011.4 0z",
  logout: "M7 3a1 1 0 00-1 1v12a1 1 0 001 1h4a1 1 0 100-2H8V5h3a1 1 0 100-2H7zm7.29 3.29a1 1 0 011.42 0l3 3a1 1 0 010 1.42l-3 3a1 1 0 01-1.42-1.42L15.59 11H9a1 1 0 110-2h6.59l-1.3-1.29a1 1 0 010-1.42z",
};

const path = paths[props.name] ?? "";
</script>

<template>
  <svg :width="size" :height="size" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
    <path :d="path" />
  </svg>
</template>
```

- [ ] **Step 2: Create `SkeletonBlock.vue`**

```vue
<script setup>
defineProps({
  lines: { type: Number, default: 3 },
});
</script>

<template>
  <div>
    <div
      v-for="n in lines"
      :key="n"
      class="skeleton-block"
      :style="{ width: n === lines ? '60%' : '100%' }"
    ></div>
  </div>
</template>
```

- [ ] **Step 3: Create `EmptyState.vue`**

```vue
<script setup>
defineProps({
  hint: { type: String, default: "" },
});
</script>

<template>
  <div class="empty-state">
    <p>{{ hint }}</p>
  </div>
</template>
```

- [ ] **Step 4: Create `MediaItemRow.vue`**

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
    <div>
      <div class="media-item-title">{{ title }}</div>
      <div v-if="subtitle" class="media-item-subtitle">{{ subtitle }}</div>
    </div>
  </div>
</template>
```

- [ ] **Step 5: Verify**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: builds without errors. (These 4 files aren't imported anywhere yet, so Vite won't even compile them as part of the entry graph — this build just confirms the rest of the app still builds; the files themselves get compiled and exercised for real starting Task 5.)

Run: `cd spotify_explorer && pytest -v`
Expected: all 55 tests pass.

- [ ] **Step 6: Commit**

```bash
git add spotify_explorer/frontend/src/components/Icon.vue spotify_explorer/frontend/src/components/SkeletonBlock.vue spotify_explorer/frontend/src/components/EmptyState.vue spotify_explorer/frontend/src/components/MediaItemRow.vue
git commit -m "feat: add Icon, SkeletonBlock, EmptyState, MediaItemRow components"
```

---

## Task 3: `spotifyShapes.js`, `useHistory.js`, and `useApi.js`'s new `loading` state

**Files:**
- Create: `spotify_explorer/frontend/src/utils/spotifyShapes.js`
- Create: `spotify_explorer/frontend/src/composables/useHistory.js`
- Modify: `spotify_explorer/frontend/src/composables/useApi.js`

- [ ] **Step 1: Create `src/utils/spotifyShapes.js`**

Three pure functions extracting `{image, title, subtitle}` from raw Spotify track/artist/album objects, each defensive against missing fields (partial data, error bodies, or fields Spotify omits when a scope/quota restriction applies) — returns `null` when the object doesn't look like the expected shape, so callers can safely skip rendering a preview and fall back to the raw JSON:

```javascript
export function trackSummary(track) {
  if (!track || !track.name) return null;
  return {
    image: track.album?.images?.[0]?.url ?? null,
    title: track.name,
    subtitle: (track.artists ?? []).map((a) => a.name).join(", "),
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
        : (artist.genres ?? []).join(", "),
  };
}

export function albumSummary(album) {
  if (!album || !album.name) return null;
  return {
    image: album.images?.[0]?.url ?? null,
    title: album.name,
    subtitle: (album.artists ?? []).map((a) => a.name).join(", "),
  };
}
```

- [ ] **Step 2: Create `src/composables/useHistory.js`**

localStorage-backed "recent queries" per tab, defensive against `localStorage` being unavailable (private browsing, disabled storage) — falls back to an empty, non-persisted list rather than throwing:

```javascript
import { ref } from "vue";

function readStorage(key) {
  try {
    return JSON.parse(localStorage.getItem(key) || "[]");
  } catch {
    return [];
  }
}

function writeStorage(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // localStorage indisponível (modo privado, cota excedida, etc.) — ignora
  }
}

export function useHistory(key, limit = 10) {
  const storageKey = `spotify-explorer:history:${key}`;
  const items = ref(readStorage(storageKey));

  function add(value) {
    if (!value) return;
    items.value = [value, ...items.value.filter((v) => v !== value)].slice(0, limit);
    writeStorage(storageKey, items.value);
  }

  return { items, add };
}
```

- [ ] **Step 3: Add a `loading` field to `useApi.js`'s `status`**

Replace the entire contents of `spotify_explorer/frontend/src/composables/useApi.js` with:

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
  const status = reactive({ text: "", className: "status", loading: false });

  async function call(url, options = {}) {
    status.loading = true;
    status.text = "Carregando...";
    status.className = "status";

    const result = await fetchJSON(url, options);

    status.loading = false;
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

The only change from the current file: `status` now also carries a `loading` boolean, toggled around the fetch. `fetchJSON` is untouched. `useApi()`'s returned shape is still `{status, call}` — every existing call site (`SearchTab.vue`, `RecommendationsTab.vue`, `MeusDadosTab.vue`) keeps working unmodified, they just now also have `status.loading` available (used starting Task 7).

**Design note for later tasks:** `loading` lives INSIDE the `status` reactive object rather than as a separate returned `ref`, specifically so that accessing it through a property chain (e.g. `someNamedInstance.status.loading`, needed in Task 10 where `MeusDadosTab.vue` holds three separate `useApi()` instances under names like `top`/`saved`/`recentlyPlayed`) always works correctly. A plain `ref` returned as a second top-level property would only auto-unwrap in Vue templates when destructured directly into a component's own top-level `<script setup>` bindings (works fine for `SearchTab`/`RecommendationsTab`, which do exactly that) — accessed via a property chain like `top.loading` instead of a bare `loading` binding, a `ref` does NOT auto-unwrap and the template would receive the raw `Ref` object (always truthy) instead of its boolean value, silently breaking any `v-if`. Keeping `loading` as a plain field on the already-`reactive()` `status` object sidesteps this entirely — nested plain properties on a `reactive()` proxy always resolve correctly in templates, however they're accessed. `Track`/`Artist` tabs (Task 8-9), which manage their own `status` object manually (not via `useApi()`, since they aggregate several parallel calls), follow the same pattern: `reactive({text, className, loading})`.

- [ ] **Step 4: Verify**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: builds without errors.

Run: `cd spotify_explorer && pytest -v`
Expected: all 55 tests pass.

- [ ] **Step 5: Commit**

```bash
git add spotify_explorer/frontend/src/utils/spotifyShapes.js spotify_explorer/frontend/src/composables/useHistory.js spotify_explorer/frontend/src/composables/useApi.js
git commit -m "feat: add spotifyShapes utils, useHistory composable, and loading state to useApi"
```

---

## Task 4: `JsonViewer.vue` — color by value type

**Files:**
- Modify: `spotify_explorer/frontend/src/components/JsonViewer.vue`

- [ ] **Step 1: Replace the file**

Replace the entire contents of `spotify_explorer/frontend/src/components/JsonViewer.vue` with:

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

function primitiveClass(value) {
  if (value === null || value === undefined) return "json-null";
  if (typeof value === "string") return "json-string";
  if (typeof value === "number") return "json-number";
  if (typeof value === "boolean") return "json-boolean";
  return "";
}
</script>

<template>
  <template v-if="data === null || data === undefined">
    <span class="json-null">null</span>
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
    <span :class="primitiveClass(data)">{{ JSON.stringify(data) }}</span>
  </template>
</template>
```

The only changes from the current file: a new `primitiveClass(value)` function, and the two leaf-value spans (`null` and the primitive branch) now carry a type-based class (`.json-string`/`.json-number`/`.json-boolean`/`.json-null`, styled in Task 1's CSS). The recursive structure, `isContainer`/`entries`/`brackets`, and every other behavior are unchanged.

- [ ] **Step 2: Verify**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: builds without errors.

Run: `cd spotify_explorer && pytest -v`
Expected: all 55 tests pass.

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/components/JsonViewer.vue
git commit -m "feat: colorize JSON values by type in JsonViewer"
```

---

## Task 5: `ResultPanel.vue`

**Files:**
- Create: `spotify_explorer/frontend/src/components/ResultPanel.vue`

The shared wrapper every tab uses starting Task 7: shows a loading skeleton, an empty-state hint, or (once there's data) an optional `#preview` slot + the status pill + a "Copiar JSON" button + the full `JsonViewer`.

- [ ] **Step 1: Create the file**

```vue
<script setup>
import { ref } from "vue";
import Icon from "./Icon.vue";
import SkeletonBlock from "./SkeletonBlock.vue";
import EmptyState from "./EmptyState.vue";
import JsonViewer from "./JsonViewer.vue";

const props = defineProps({
  status: { type: Object, required: true },
  data: { type: null, default: null },
  emptyHint: { type: String, default: "" },
});

const copied = ref(false);

async function copyJSON() {
  try {
    await navigator.clipboard.writeText(JSON.stringify(props.data, null, 2));
    copied.value = true;
    setTimeout(() => {
      copied.value = false;
    }, 2000);
  } catch (err) {
    // clipboard indisponível (permissão negada, contexto não seguro) — ignora
  }
}
</script>

<template>
  <div>
    <SkeletonBlock v-if="status.loading" />
    <EmptyState v-else-if="data === null" :hint="emptyHint" />
    <div v-else>
      <slot name="preview" />
      <div class="result-panel-header">
        <p :class="status.className">{{ status.text }}</p>
        <button type="button" class="btn btn-secondary" @click="copyJSON">
          <Icon :name="copied ? 'check' : 'copy'" :size="14" />
          {{ copied ? "Copiado!" : "Copiar JSON" }}
        </button>
      </div>
      <div class="result">
        <JsonViewer :data="data" />
      </div>
    </div>
  </div>
</template>
```

`status` must be an object shaped like `{text, className, loading}` — exactly what `useApi()` (Task 3) returns, and what `Track`/`Artist` tabs (Tasks 8-9) build manually. Note there's no separate `loading` prop here even though the spec's prose describes "status pill + loading" as conceptually two things — `loading` is read from `status.loading` (see Task 3's design note for why it's nested inside `status` rather than a sibling prop: it avoids a real Vue ref-unwrapping bug in `MeusDadosTab.vue`, Task 10, which holds several named `useApi()` instances at once). The `#preview` slot is optional — a tab that doesn't provide one still gets the status pill, copy button, and raw `JsonViewer`, just no rich preview above them (this is the safe fallback for any response shape `spotifyShapes.js` doesn't recognize).

- [ ] **Step 2: Verify**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: builds without errors. (Not imported by anything yet — Task 7 is the first real consumer.)

Run: `cd spotify_explorer && pytest -v`
Expected: all 55 tests pass.

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/components/ResultPanel.vue
git commit -m "feat: add ResultPanel component (status, copy, skeleton, empty state, JSON)"
```

---

## Task 6: Sidebar layout — `AppSidebar.vue` and `App.vue`

**Files:**
- Create: `spotify_explorer/frontend/src/components/AppSidebar.vue`
- Modify: `spotify_explorer/frontend/src/App.vue`

Replaces the top tab-nav + header with a fixed left sidebar. This is the task where the app visually becomes "the redesign" for the first time — after this, all 5 tabs are still the OLD (pre-redesign) markup rendered inside the new shell, which is fine (Tasks 7-10 bring them up to date one by one).

- [ ] **Step 1: Create `AppSidebar.vue`**

```vue
<script setup>
import Icon from "./Icon.vue";

defineProps({
  tabs: { type: Array, required: true },
  activeTab: { type: String, required: true },
  authState: { type: Object, required: true },
});

const emit = defineEmits(["select"]);
</script>

<template>
  <aside class="app-sidebar">
    <div>
      <div class="app-sidebar-title">
        <Icon name="waveform" :size="18" />
        Spotify API Explorer
      </div>
      <div class="app-sidebar-subtitle">Dev tool — não é o produto Spotify</div>
    </div>

    <nav class="sidebar-nav">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        class="sidebar-nav-item"
        :class="{ active: activeTab === tab.id }"
        @click="emit('select', tab.id)"
      >
        <Icon :name="tab.icon" :size="18" />
        {{ tab.label }}
      </button>
    </nav>

    <div class="sidebar-footer">
      <div v-if="authState.loggedIn" class="sidebar-user">
        <span>{{ authState.profile.display_name || authState.profile.id }}</span>
        <a href="/logout" class="btn btn-secondary">
          <Icon name="logout" :size="14" />
          Desconectar
        </a>
      </div>
      <a v-else href="/login" class="btn">Conectar Spotify</a>
    </div>
  </aside>
</template>
```

- [ ] **Step 2: Replace `App.vue`**

Replace the entire contents of `spotify_explorer/frontend/src/App.vue` with:

```vue
<script setup>
import { onMounted, reactive, ref } from "vue";
import { fetchJSON } from "./composables/useApi.js";
import { useAuthStatus } from "./composables/useAuthStatus.js";
import AppSidebar from "./components/AppSidebar.vue";
import SearchTab from "./tabs/SearchTab.vue";
import TrackTab from "./tabs/TrackTab.vue";
import ArtistTab from "./tabs/ArtistTab.vue";
import RecommendationsTab from "./tabs/RecommendationsTab.vue";
import MeusDadosTab from "./tabs/MeusDadosTab.vue";

const tabs = [
  { id: "search", label: "Search", icon: "search", component: SearchTab },
  { id: "track", label: "Track & Audio", icon: "disc", component: TrackTab },
  { id: "artist", label: "Artist", icon: "mic", component: ArtistTab },
  { id: "recommendations", label: "Recommendations", icon: "sparkles", component: RecommendationsTab },
  { id: "me", label: "Meus dados", icon: "heart", component: MeusDadosTab },
];

const activeTab = ref("search");
const config = reactive({ missingCredentials: false });
const authError = ref(new URLSearchParams(window.location.search).get("auth_error"));
const { state: authState, refresh: refreshAuthStatus } = useAuthStatus();

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

Same `tabs`/`activeTab`/`KeepAlive`/`config`/`authError`/`useAuthStatus` wiring as before — only the template markup changed (sidebar instead of a top `<nav class="tabs">`, no more `<header>`/`#user-status` div, login/logout links now live in `AppSidebar`'s footer instead of inside `MeusDadosTab.vue` — Task 10 removes the now-redundant login/logout links from that tab).

- [ ] **Step 3: Verify**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: builds without errors.

Run: `cd spotify_explorer && pytest -v`
Expected: all 55 tests pass.

- [ ] **Step 4: Commit**

```bash
git add spotify_explorer/frontend/src/components/AppSidebar.vue spotify_explorer/frontend/src/App.vue
git commit -m "feat: replace top tab-nav with a sidebar layout"
```

---

## Task 7: Rewrite `SearchTab.vue` and `RecommendationsTab.vue`

**Files:**
- Modify: `spotify_explorer/frontend/src/tabs/SearchTab.vue`
- Modify: `spotify_explorer/frontend/src/tabs/RecommendationsTab.vue`

Both tabs return a flat list of one media type — `SearchTab` returns tracks/artists/albums depending on the chosen `type`, `RecommendationsTab` always returns tracks. Both get: a history-chips row, the existing form unchanged, and `ResultPanel` with a `#preview` slot rendering a `MediaItemRow` per result.

- [ ] **Step 1: Replace `SearchTab.vue`**

```vue
<script setup>
import { computed, reactive } from "vue";
import { useApi } from "../composables/useApi.js";
import { useHistory } from "../composables/useHistory.js";
import { trackSummary, artistSummary, albumSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const form = reactive({ q: "", type: "track", limit: 10 });
const { status, call } = useApi();
const result = reactive({ data: null });
const { items: history, add: addToHistory } = useHistory("search");

const summaryFn = { track: trackSummary, artist: artistSummary, album: albumSummary };

const items = computed(() => {
  if (!result.data) return [];
  const list = result.data[`${form.type}s`]?.items ?? [];
  const summarize = summaryFn[form.type];
  return list.map(summarize).filter((item) => item !== null);
});

async function onSubmit() {
  const { data } = await call("/api/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ q: form.q, type: form.type, limit: Number(form.limit) }),
  });
  result.data = data;
  addToHistory(form.q);
}
</script>

<template>
  <section>
    <h2>Search</h2>
    <div v-if="history.length" class="history-chips">
      <button v-for="item in history" :key="item" type="button" class="history-chip" @click="form.q = item">
        {{ item }}
      </button>
    </div>
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
      <button type="submit" class="btn">Buscar</button>
    </form>
    <ResultPanel
      :status="status"
      :data="result.data"
      empty-hint="Digite um termo e escolha o tipo pra buscar no catálogo"
    >
      <template #preview>
        <div v-for="(item, i) in items" :key="i">
          <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" />
        </div>
      </template>
    </ResultPanel>
  </section>
</template>
```

- [ ] **Step 2: Replace `RecommendationsTab.vue`**

```vue
<script setup>
import { computed, reactive } from "vue";
import { useApi } from "../composables/useApi.js";
import { useHistory } from "../composables/useHistory.js";
import { trackSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const form = reactive({
  seed_genres: "",
  seed_tracks: "",
  seed_artists: "",
  target_energy: "",
  target_valence: "",
});
const { status, call } = useApi();
const result = reactive({ data: null });
const { items: history, add: addToHistory } = useHistory("recommendations");

const items = computed(() => {
  if (!result.data) return [];
  return (result.data.tracks ?? []).map(trackSummary).filter((item) => item !== null);
});

async function onSubmit() {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(form)) {
    if (value) params.set(key, value);
  }
  const { data } = await call(`/api/recommendations?${params}`);
  result.data = data;
  const seedSummary = form.seed_genres || form.seed_tracks || form.seed_artists;
  if (seedSummary) addToHistory(seedSummary);
}
</script>

<template>
  <section>
    <h2>Recommendations</h2>
    <div v-if="history.length" class="history-chips">
      <button v-for="item in history" :key="item" type="button" class="history-chip" @click="form.seed_genres = item">
        {{ item }}
      </button>
    </div>
    <form @submit.prevent="onSubmit">
      <label>Seed genres (csv) <input type="text" v-model="form.seed_genres" placeholder="pop,rock"></label>
      <label>Seed tracks (csv) <input type="text" v-model="form.seed_tracks"></label>
      <label>Seed artists (csv) <input type="text" v-model="form.seed_artists"></label>
      <label>Target energy (0-1) <input type="number" v-model="form.target_energy" step="0.1" min="0" max="1"></label>
      <label>Target valence (0-1) <input type="number" v-model="form.target_valence" step="0.1" min="0" max="1"></label>
      <button type="submit" class="btn">Buscar recomendações</button>
    </form>
    <ResultPanel
      :status="status"
      :data="result.data"
      empty-hint="Preencha ao menos um seed (genre/track/artist)"
    >
      <template #preview>
        <div v-for="(item, i) in items" :key="i">
          <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" />
        </div>
      </template>
    </ResultPanel>
  </section>
</template>
```

The history chip in `RecommendationsTab` re-fills the `seed_genres` field specifically (whichever seed field was non-empty on the last successful submit) — a deliberate simplification given the form has 5 fields; re-filling all 5 from one history entry would need storing structured objects instead of single strings, which isn't worth the complexity for a "recent seeds" convenience feature.

- [ ] **Step 3: Verify**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: builds without errors.

Run: `cd spotify_explorer && pytest -v`
Expected: all 55 tests pass.

- [ ] **Step 4: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/SearchTab.vue spotify_explorer/frontend/src/tabs/RecommendationsTab.vue
git commit -m "feat: redesign Search and Recommendations tabs with previews and history"
```

---

## Task 8: Rewrite `TrackTab.vue` with `TrackPreview.vue`

**Files:**
- Create: `spotify_explorer/frontend/src/components/previews/TrackPreview.vue`
- Modify: `spotify_explorer/frontend/src/tabs/TrackTab.vue`

- [ ] **Step 1: Create `TrackPreview.vue`**

Hero card: cover art, track name, artist(s), duration, and (when not 403'd) 3 simple bars for danceability/energy/valence:

```vue
<script setup>
import { computed } from "vue";
import { trackSummary } from "../../utils/spotifyShapes.js";

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
      <div class="preview-title">{{ summary.title }}</div>
      <div class="preview-subtitle">{{ summary.subtitle }}</div>
      <div v-if="track.duration_ms" class="preview-subtitle">{{ formatDuration(track.duration_ms) }}</div>
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

- [ ] **Step 2: Replace `TrackTab.vue`**

`fetchJSON`/`Promise.all` aggregation stays exactly as it is today (established, already-reviewed pattern for combining 3 parallel calls into one status) — this task only adds the history chips, the `loading`/`status` shape ResultPanel expects, and the `TrackPreview` in the `#preview` slot:

```vue
<script setup>
import { reactive, ref } from "vue";
import { fetchJSON } from "../composables/useApi.js";
import { useHistory } from "../composables/useHistory.js";
import ResultPanel from "../components/ResultPanel.vue";
import TrackPreview from "../components/previews/TrackPreview.vue";

const trackId = ref("");
const status = reactive({ text: "", className: "status", loading: false });
const result = reactive({ data: null });
const { items: history, add: addToHistory } = useHistory("track");

async function onSubmit() {
  status.loading = true;
  status.text = "Carregando...";
  status.className = "status";

  const [track, audioFeatures, audioAnalysis] = await Promise.all([
    fetchJSON(`/api/track/${trackId.value}`),
    fetchJSON(`/api/audio-features/${trackId.value}`),
    fetchJSON(`/api/audio-analysis/${trackId.value}`),
  ]);

  status.loading = false;
  const results = [track, audioFeatures, audioAnalysis];
  const allOk = results.every((r) => r.ok);
  const statuses = results.map((r) => (r.status === 0 ? "erro de rede" : r.status)).join(", ");
  status.text = `HTTP ${statuses}`;
  status.className = "status " + (allOk ? "status-ok" : "status-error");
  result.data = {
    track: track.data,
    audio_features: audioFeatures.data,
    audio_analysis: audioAnalysis.data,
  };
  addToHistory(trackId.value);
}
</script>

<template>
  <section>
    <h2>Track & Audio</h2>
    <div v-if="history.length" class="history-chips">
      <button v-for="item in history" :key="item" type="button" class="history-chip" @click="trackId = item">
        {{ item }}
      </button>
    </div>
    <form @submit.prevent="onSubmit">
      <label>Track ID <input type="text" v-model="trackId" required placeholder="ex: 11dFghVXANMlKmJXsNCbNl"></label>
      <button type="submit" class="btn">Buscar track + audio-features + audio-analysis</button>
    </form>
    <ResultPanel
      :status="status"
      :data="result.data"
      empty-hint="Cole um Track ID, ex: 11dFghVXANMlKmJXsNCbNl"
    >
      <template #preview>
        <TrackPreview :track="result.data.track" :audio-features="result.data.audio_features" />
      </template>
    </ResultPanel>
  </section>
</template>
```

`result.data` is only ever `null` before the first submit (`ResultPanel` shows the `EmptyState` in that case, so the `#preview` slot — and its `result.data.track` access — is never evaluated then). After a submit, `result.data` is always the `{track, audio_features, audio_analysis}` object (even if some/all of the 3 parallel calls failed, since each failure still produces a `.data` value — an error body or `null`), so `result.data.track`/`result.data.audio_features` are always safe to read.

- [ ] **Step 3: Verify**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: builds without errors.

Run: `cd spotify_explorer && pytest -v`
Expected: all 55 tests pass.

- [ ] **Step 4: Commit**

```bash
git add spotify_explorer/frontend/src/components/previews/TrackPreview.vue spotify_explorer/frontend/src/tabs/TrackTab.vue
git commit -m "feat: redesign Track & Audio tab with TrackPreview and audio-feature bars"
```

---

## Task 9: Rewrite `ArtistTab.vue` with `ArtistPreview.vue`

**Files:**
- Create: `spotify_explorer/frontend/src/components/previews/ArtistPreview.vue`
- Modify: `spotify_explorer/frontend/src/tabs/ArtistTab.vue`

- [ ] **Step 1: Create `ArtistPreview.vue`**

Hero card: photo, name, genre chips, followers:

```vue
<script setup>
import { computed } from "vue";
import { artistSummary } from "../../utils/spotifyShapes.js";

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
    </div>
  </div>
</template>
```

- [ ] **Step 2: Replace `ArtistTab.vue`**

Same `Promise.all` aggregation as today, plus history chips, `ArtistPreview`, and `MediaItemRow` lists for top tracks and related artists:

```vue
<script setup>
import { computed, reactive, ref } from "vue";
import { fetchJSON } from "../composables/useApi.js";
import { useHistory } from "../composables/useHistory.js";
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
</script>

<template>
  <section>
    <h2>Artist</h2>
    <div v-if="history.length" class="history-chips">
      <button v-for="item in history" :key="item" type="button" class="history-chip" @click="artistId = item">
        {{ item }}
      </button>
    </div>
    <form @submit.prevent="onSubmit">
      <label>Artist ID <input type="text" v-model="artistId" required placeholder="ex: 0TnOYISbd1XYRBk9myaseg"></label>
      <button type="submit" class="btn">Buscar artist + top-tracks + albums + related-artists</button>
    </form>
    <ResultPanel
      :status="status"
      :data="result.data"
      empty-hint="Cole um Artist ID, ex: 0TnOYISbd1XYRBk9myaseg"
    >
      <template #preview>
        <ArtistPreview :artist="result.data.artist" />
        <div v-if="topTracksItems.length">
          <h3>Top tracks</h3>
          <div v-for="(item, i) in topTracksItems" :key="i">
            <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" />
          </div>
        </div>
        <div v-if="relatedArtistsItems.length">
          <h3>Related artists</h3>
          <div v-for="(item, i) in relatedArtistsItems" :key="i">
            <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" />
          </div>
        </div>
      </template>
    </ResultPanel>
  </section>
</template>
```

`albums` (fetched, included in the raw JSON below the preview) has no dedicated preview per the spec — only `artist`, `top_tracks`, and `related_artists` get rich rendering; `albums` stays visible in the raw JSON panel, same as any other field not covered by a `*Summary` function.

- [ ] **Step 3: Verify**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: builds without errors.

Run: `cd spotify_explorer && pytest -v`
Expected: all 55 tests pass.

- [ ] **Step 4: Commit**

```bash
git add spotify_explorer/frontend/src/components/previews/ArtistPreview.vue spotify_explorer/frontend/src/tabs/ArtistTab.vue
git commit -m "feat: redesign Artist tab with ArtistPreview, top tracks, and related artists"
```

---

## Task 10: Rewrite `MeusDadosTab.vue`

**Files:**
- Modify: `spotify_explorer/frontend/src/tabs/MeusDadosTab.vue`

Three independent `useApi()` instances (unchanged pattern from before), each now rendering through `ResultPanel` with a `MediaItemRow` list. The login/logout links move to `AppSidebar` (Task 6) — this tab no longer renders its own "Conectar Spotify"/"Desconectar" link when logged in, only the logged-out message + a login button (kept here too, since a user landing straight on this tab while logged out should still have an obvious way to log in without hunting for the sidebar).

- [ ] **Step 1: Replace the file**

```vue
<script setup>
import { computed, reactive } from "vue";
import { useApi } from "../composables/useApi.js";
import { useAuthStatus } from "../composables/useAuthStatus.js";
import { trackSummary, artistSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const { state: authState } = useAuthStatus();

const timeRange = reactive({ value: "medium_term" });
const topTarget = reactive({ value: "tracks" });

const top = useApi();
const topResult = reactive({ data: null });

const saved = useApi();
const savedResult = reactive({ data: null });

const recentlyPlayed = useApi();
const recentlyPlayedResult = reactive({ data: null });

const topItems = computed(() => {
  if (!topResult.data?.items) return [];
  const summarize = topTarget.value === "artists" ? artistSummary : trackSummary;
  return topResult.data.items.map(summarize).filter((item) => item !== null);
});

const savedItems = computed(() => {
  if (!savedResult.data?.items) return [];
  return savedResult.data.items.map((item) => trackSummary(item.track)).filter((item) => item !== null);
});

const recentlyPlayedItems = computed(() => {
  if (!recentlyPlayedResult.data?.items) return [];
  return recentlyPlayedResult.data.items.map((item) => trackSummary(item.track)).filter((item) => item !== null);
});

async function fetchTop(target) {
  topTarget.value = target;
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
    <h2>Meus dados</h2>
    <div v-if="!authState.loggedIn">
      <p>Nenhum usuário conectado.</p>
      <a class="btn" href="/login">Conectar Spotify</a>
    </div>
    <div v-else>
      <p>Logado como: {{ authState.profile.display_name || authState.profile.id }}</p>

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
          <button type="button" class="btn" @click="fetchTop('tracks')">Top tracks</button>
          <button type="button" class="btn" @click="fetchTop('artists')">Top artists</button>
        </form>
        <ResultPanel :status="top.status" :data="topResult.data" empty-hint="Clique em Top tracks ou Top artists">
          <template #preview>
            <div v-for="(item, i) in topItems" :key="i">
              <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" />
            </div>
          </template>
        </ResultPanel>
      </fieldset>

      <fieldset>
        <legend>Faixas curtidas</legend>
        <button type="button" class="btn" @click="fetchSaved">Buscar curtidas</button>
        <ResultPanel :status="saved.status" :data="savedResult.data" empty-hint="Clique em Buscar curtidas">
          <template #preview>
            <div v-for="(item, i) in savedItems" :key="i">
              <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" />
            </div>
          </template>
        </ResultPanel>
      </fieldset>

      <fieldset>
        <legend>Tocadas recentemente</legend>
        <button type="button" class="btn" @click="fetchRecentlyPlayed">Buscar recentes (máx. 50)</button>
        <ResultPanel
          :status="recentlyPlayed.status"
          :data="recentlyPlayedResult.data"
          empty-hint="Clique em Buscar recentes"
        >
          <template #preview>
            <div v-for="(item, i) in recentlyPlayedItems" :key="i">
              <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" />
            </div>
          </template>
        </ResultPanel>
      </fieldset>
    </div>
  </section>
</template>
```

`top.status`/`saved.status`/`recentlyPlayed.status` are each a `reactive()` object (from `useApi()`, Task 3) — passed straight to `ResultPanel` via property-chain access (`top.status`, not `top.status.value`), which works correctly since `status` is `reactive()`, not a `ref` (see Task 3's design note). "Recently played" items come back as `{items: [{track: {...}, played_at: "..."}]}` — `recentlyPlayedItems` unwraps `item.track` before calling `trackSummary`, unlike `topItems`/`savedItems` where the API already returns track/artist objects directly in `items[]`.

- [ ] **Step 2: Verify**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: builds without errors.

Run: `cd spotify_explorer && pytest -v`
Expected: all 55 tests pass.

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/MeusDadosTab.vue
git commit -m "feat: redesign Meus dados tab with MediaItemRow lists for all 3 sections"
```

---

## Task 11: Remove dead CSS and final verification

**Files:**
- Modify: `spotify_explorer/frontend/src/style.css`

**No files:** verification only, after the CSS cleanup.

After Task 6 replaced the top `<nav class="tabs">`/`<header>` markup with the sidebar, three rules from the ORIGINAL (pre-redesign) part of `style.css` became dead: `header {...}`, `.tabs {...}`, `.tab-button`/`.tab-button.active {...}`. Every other original rule (`.banner`, `.banner-error`, `form`, `label`, `fieldset`, `.button, button`, `.status`, `.status-ok`, `.status-error`, `.result`, `.json-indent`, `.json-key`) is still in active use by the redesigned components and stays untouched.

- [ ] **Step 1: Confirm the 3 rules are genuinely unused**

Run: `grep -rn "class=\"tabs\"\|tab-button\|<header" spotify_explorer/frontend/src`
Expected: no output (no `.vue` file references any of these anymore — `App.vue` was rewritten in Task 6, and nothing else ever used them).

- [ ] **Step 2: Remove the 3 dead rules from `style.css`**

Delete these blocks from the ORIGINAL (top) part of `spotify_explorer/frontend/src/style.css` — they're near the top of the file, before the "Spotify-branded redesign" section added in Task 1:

```css
header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
```

```css
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
```

Leave every other rule in the file untouched, including the original `:root { color-scheme: light dark; --accent: #1db954; --border: #ccc; --error: #c0392b; }` block — `--accent`/`--border`/`--error` are still referenced by name in rules that remain in use (`.banner-error`, `.status-ok`, `.status-error`), and the new tokens block added in Task 1 lives separately further down the file.

- [ ] **Step 3: Full verification**

Run: `cd spotify_explorer/frontend && rm -rf node_modules ../static/frontend && npm install && npm run build`
Expected: clean install and build succeed with no errors, `spotify_explorer/static/frontend/index.html` + `assets/` regenerated.

Run: `cd spotify_explorer && pytest -v`
Expected: all 55 tests pass.

Run: `pytest tests -v` (from repo root)
Expected: all 18 pre-existing, unrelated tests pass.

Run: `git status` (from repo root)
Expected: nothing to commit, working tree clean, all work committed on `feature/spotify-api-explorer`.

- [ ] **Step 4: Commit the CSS cleanup**

```bash
git add spotify_explorer/frontend/src/style.css
git commit -m "chore: remove dead CSS rules superseded by the sidebar redesign"
```

- [ ] **Step 5: Manual smoke test (requires a human with real Spotify credentials and a browser)**

Run `python app.py` (after `npm run build`, or `npm run dev` for hot-reload — see `spotify_explorer/README.md`), open the app, and confirm:
- Sidebar renders with all 5 nav items, active state follows the selected tab, switching tabs preserves each tab's form input and results (`KeepAlive`)
- Search: submitting shows a skeleton, then a list of tracks/artists/albums with cover art (depending on `type`), then the raw JSON below; a submitted query appears as a history chip on reload of the tab
- Track & Audio: shows the cover/name/artist/duration hero card, and (if the app has Extended Quota) the 3 audio-feature bars; without Extended Quota, the 403 still shows in the raw JSON and the bars simply don't render (not a crash)
- Artist: hero card + top tracks list + related artists list
- Recommendations: list of recommended tracks (or 403, same Extended Quota caveat)
- Meus dados: login via the sidebar button, confirm the sidebar footer and this tab both reflect the logged-in state without a page reload (this exercises `useAuthStatus`'s shared singleton across `App.vue`/`AppSidebar` and this tab); top tracks/artists across all 3 time ranges, saved tracks, and recently played all render as lists; logout via the sidebar returns to the logged-out state everywhere
- "Copiar JSON" button on any result copies valid, pretty-printed JSON to the clipboard and shows "Copiado!" briefly
- Resize the browser narrower than ~768px and confirm the sidebar collapses to a horizontal bar without the page becoming unusable
