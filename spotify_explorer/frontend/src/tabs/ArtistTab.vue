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
            <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" />
          </div>
        </div>
        <div v-if="relatedArtistsItems.length">
          <h3>Related artists</h3>
          <div v-for="(item, i) in relatedArtistsItems" :key="i">
            <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" />
          </div>
        </div>
      </template>
    </ResultPanel>
  </section>
</template>
