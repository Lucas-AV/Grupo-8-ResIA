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
