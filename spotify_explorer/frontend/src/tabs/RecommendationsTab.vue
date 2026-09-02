<script setup>
import { reactive } from "vue";
import { useApi } from "../composables/useApi.js";
import JsonViewer from "../components/JsonViewer.vue";

const form = reactive({
  seed_genres: "",
  seed_tracks: "",
  seed_artists: "",
  target_energy: "",
  target_valence: "",
});
const { status, call } = useApi();
const result = reactive({ data: null });

async function onSubmit() {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(form)) {
    if (value) params.set(key, value);
  }
  const { data } = await call(`/api/recommendations?${params}`);
  result.data = data;
}
</script>

<template>
  <section>
    <form @submit.prevent="onSubmit">
      <label>Seed genres (csv) <input type="text" v-model="form.seed_genres" placeholder="pop,rock"></label>
      <label>Seed tracks (csv) <input type="text" v-model="form.seed_tracks"></label>
      <label>Seed artists (csv) <input type="text" v-model="form.seed_artists"></label>
      <label>Target energy (0-1) <input type="number" v-model="form.target_energy" step="0.1" min="0" max="1"></label>
      <label>Target valence (0-1) <input type="number" v-model="form.target_valence" step="0.1" min="0" max="1"></label>
      <button type="submit">Buscar recomendações</button>
    </form>
    <p :class="status.className">{{ status.text }}</p>
    <div class="result"><JsonViewer v-if="result.data !== null" :data="result.data" /></div>
  </section>
</template>
