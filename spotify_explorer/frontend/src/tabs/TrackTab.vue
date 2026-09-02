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
