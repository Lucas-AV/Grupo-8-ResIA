<script setup>
import { reactive, ref } from "vue";
import { fetchJSON } from "../composables/useApi.js";
import JsonViewer from "../components/JsonViewer.vue";

const artistId = ref("");
const status = reactive({ text: "", className: "status" });
const result = reactive({ data: null });

async function onSubmit() {
  status.text = "Carregando...";
  status.className = "status";

  const [artist, topTracks, albums, relatedArtists] = await Promise.all([
    fetchJSON(`/api/artist/${artistId.value}`),
    fetchJSON(`/api/artist/${artistId.value}/top-tracks`),
    fetchJSON(`/api/artist/${artistId.value}/albums`),
    fetchJSON(`/api/artist/${artistId.value}/related-artists`),
  ]);

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
}
</script>

<template>
  <section>
    <form @submit.prevent="onSubmit">
      <label>Artist ID <input type="text" v-model="artistId" required placeholder="ex: 0TnOYISbd1XYRBk9myaseg"></label>
      <button type="submit">Buscar artist + top-tracks + albums + related-artists</button>
    </form>
    <p :class="status.className">{{ status.text }}</p>
    <div class="result"><JsonViewer v-if="result.data !== null" :data="result.data" /></div>
  </section>
</template>
