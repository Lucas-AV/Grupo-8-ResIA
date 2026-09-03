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
