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
          <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" />
        </div>
      </template>
    </ResultPanel>
  </section>
</template>
