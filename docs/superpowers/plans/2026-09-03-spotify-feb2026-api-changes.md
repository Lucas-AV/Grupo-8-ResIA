# Spotify Feb/2026 API Changes — Adaptation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adapt the Playlist tab to Spotify's Feb 2026 API response-shape change (`tracks` → `items`, faixas ausentes pra playlists que o app não possui/colabora) and document the newly-removed `GET /artists/{id}/top-tracks` endpoint — no backend changes needed for either.

**Architecture:** `PlaylistTab.vue`'s `tracks` computed reads from either JSON shape Spotify might return; a new `tracksUnavailable` computed distinguishes "no faixas field at all" (API restriction) from "playlist genuinely has zero tracks" (normal). `PlaylistPreview.vue`'s track-count display falls back between the two field names. Artist tab needs no code change — its existing null-safe computed already degrades gracefully.

**Tech Stack:** Vue 3 `<script setup>` (frontend only — no backend/Python changes, no new tests, matching this project's established "no JS test suite, verify via build" convention).

---

## Task 1: Adapt `PlaylistTab.vue` to both response shapes

**Files:**
- Modify: `spotify_explorer/frontend/src/tabs/PlaylistTab.vue`

- [ ] **Step 1: Replace the `tracks` computed and add `tracksUnavailable`**

Current file (for reference, so you can locate the exact block to replace):

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

Replace the full file with:

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

const tracksContainer = computed(() => result.data?.items ?? result.data?.tracks ?? null);

const tracks = computed(() => {
  const items = tracksContainer.value?.items;
  if (!Array.isArray(items)) return [];
  return items
    .map((entry) => trackSummary(entry.item ?? entry.track))
    .filter((item) => item !== null);
});

const tracksUnavailable = computed(() => {
  if (!result.data?.name) return false;
  return !Array.isArray(tracksContainer.value?.items);
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
        <p v-else-if="tracksUnavailable" class="status status-error">
          Faixas não disponíveis — a Spotify só devolve o campo de faixas pra
          quem é dono/colaborador da playlist (restrição de fev/2026). Essa
          aba usa Client Credentials Flow, sem usuário associado, então nunca
          vai ver faixas de playlist nenhuma por aqui.
        </p>
      </template>
    </ResultPanel>
  </section>
</template>
```

The only changes: `tracksContainer` computed added, `tracks` computed reworked to read from either shape, `tracksUnavailable` computed added, and one new `<p v-else-if>` line in the template. Everything else (imports, `playlistId`, `status`/`call`, `history`, `onSubmit`, `useNavigationTarget`, the form, the history chips) is unchanged.

- [ ] **Step 2: Verify the build still succeeds**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/tabs/PlaylistTab.vue
git commit -m "fix: read playlist tracks from either Spotify response shape, note when absent"
```

---

## Task 2: Fall back the faixas count in `PlaylistPreview.vue`

**Files:**
- Modify: `spotify_explorer/frontend/src/components/previews/PlaylistPreview.vue`

- [ ] **Step 1: Update the track-count line**

Current file:

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

Replace the single line:

```html
      <div v-if="playlist.tracks?.total != null" class="preview-subtitle">{{ playlist.tracks.total }} faixas</div>
```

with:

```html
      <div v-if="(playlist.items?.total ?? playlist.tracks?.total) != null" class="preview-subtitle">
        {{ playlist.items?.total ?? playlist.tracks?.total }} faixas
      </div>
```

(`items` — the new field — checked first, `tracks` as fallback, matching `PlaylistTab.vue`'s `tracksContainer` precedence for the same rename.)

No other change to this file.

- [ ] **Step 2: Verify the build still succeeds**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/frontend/src/components/previews/PlaylistPreview.vue
git commit -m "fix: fall back playlist track count to the items.total field"
```

---

## Task 3: Document both Feb/2026 findings in `spotify_explorer/README.md`

**Files:**
- Modify: `spotify_explorer/README.md`

- [ ] **Step 1: Add to "Restrições conhecidas da API"**

In `spotify_explorer/README.md`, in the "## Restrições conhecidas da API (não são bugs da ferramenta)" section, add after the existing fev/2026 New Releases paragraph (the one starting "Desde fev/2026 a Spotify removeu `GET /browse/new-releases`..."):

```markdown
Na mesma leva de fev/2026, a Spotify também removeu
`GET /artists/{id}/top-tracks` (sem substituto) e mudou o formato de
`GET /playlists/{id}`: o campo `tracks` virou `items`, e o campo de
faixas fica ausente inteiramente quando quem chama não é
dono/colaborador da playlist. A aba Artist simplesmente não mostra a
seção "Top tracks" quando isso falha (mesmo tratamento dos outros 403
já citados). A aba Playlist usa Client Credentials Flow — sem usuário
associado — então mostra uma nota explícita de "Faixas não
disponíveis" em vez da lista, já que nunca vai ter permissão de
dono/colaborador nenhuma.
```

- [ ] **Step 2: Add to the smoke-test checklist**

In "## Checklist de smoke test manual", add:

```markdown
- [ ] Artist não quebra quando top-tracks falha (403/404) — só omite
      a seção
- [ ] Playlist mostra a nota "Faixas não disponíveis" pra qualquer
      playlist pública (Client Credentials nunca é dono/colaborador)
```

- [ ] **Step 3: Commit**

```bash
git add spotify_explorer/README.md
git commit -m "docs: document artist top-tracks removal and playlist items restriction"
```

---

## Task 4: Final verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full frontend build**

Run: `cd spotify_explorer/frontend && npm run build`
Expected: build succeeds with no errors

- [ ] **Step 2: Run the full backend test suite (regression check — no backend files changed, but confirm nothing else broke)**

Run: `cd spotify_explorer && pytest -v`
Expected: all tests pass (this plan makes no backend changes, so this should be identical to before)

- [ ] **Step 3: Manual smoke test**

Start the backend (`cd spotify_explorer && python app.py`) and frontend dev server (`cd spotify_explorer/frontend && npm run dev`), open `http://127.0.0.1:5173`, and walk the 2 new checklist items added to `spotify_explorer/README.md` in Task 3 — plus re-confirm the pre-existing "Artist retorna os 4 blocos de dados" checklist item still passes in the sense of "doesn't crash," even if the top-tracks block itself is now empty.
