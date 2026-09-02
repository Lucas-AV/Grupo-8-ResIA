<script setup>
import { computed, reactive, ref } from "vue";
import { useApi } from "../composables/useApi.js";
import { useHistory } from "../composables/useHistory.js";
import { trackSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import AlbumPreview from "../components/previews/AlbumPreview.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const albumId = ref("");
const { status, call } = useApi();
const result = reactive({ data: null });
const { items: history, add: addToHistory } = useHistory("album");

const tracks = computed(() => {
  const items = result.data?.tracks?.items;
  if (!Array.isArray(items)) return [];
  return items.map(trackSummary).filter((item) => item !== null);
});

async function onSubmit() {
  const { data } = await call(`/api/album/${albumId.value}`);
  result.data = data;
  addToHistory(albumId.value);
}
</script>

<template>
  <section>
    <h2>Album</h2>
    <div v-if="history.length" class="history-chips">
      <button v-for="item in history" :key="item" type="button" class="history-chip" @click="albumId = item">
        {{ item }}
      </button>
    </div>
    <form @submit.prevent="onSubmit">
      <label>Album ID <input type="text" v-model="albumId" required placeholder="ex: 4aawyAB9vmqN3uQ7FjRGTy"></label>
      <button type="submit" class="btn">Buscar álbum</button>
    </form>
    <ResultPanel :status="status" :data="result.data" empty-hint="Cole um Album ID, ex: 4aawyAB9vmqN3uQ7FjRGTy">
      <template #preview>
        <AlbumPreview :album="result.data" />
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
