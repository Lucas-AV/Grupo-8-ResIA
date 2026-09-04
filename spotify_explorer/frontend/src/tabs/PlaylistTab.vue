<script setup>
import { computed, reactive, ref } from "vue";
import { useApi } from "../composables/useApi.js";
import { useHistory } from "../composables/useHistory.js";
import { useNavigationTarget } from "../composables/useTabNavigation.js";
import { useNowPlaying } from "../composables/useNowPlaying.js";
import { trackSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import PlaylistPreview from "../components/previews/PlaylistPreview.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const playlistId = ref("");
const { status, call } = useApi();
const result = reactive({ data: null });
const { items: history, add: addToHistory } = useHistory("playlist");
const { open } = useNowPlaying();

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
            <button type="button" class="media-item-clickable" @click="open(item)">
              <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" />
            </button>
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
