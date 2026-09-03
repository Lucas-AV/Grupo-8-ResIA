<script setup>
import { computed, reactive } from "vue";
import { useApi } from "../composables/useApi.js";
import { albumSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const form = reactive({ limit: 20 });
const { status, call } = useApi();
const result = reactive({ data: null });

const items = computed(() => {
  if (!result.data?.albums?.items) return [];
  return result.data.albums.items.map(albumSummary).filter((item) => item !== null);
});

async function onSubmit() {
  const { data } = await call(`/api/new-releases?limit=${Number(form.limit)}`);
  result.data = data;
}
</script>

<template>
  <section>
    <h2>New Releases</h2>
    <form @submit.prevent="onSubmit">
      <label>Limit <input type="number" v-model.number="form.limit" min="1" max="50"></label>
      <button type="submit" class="btn">Buscar lançamentos</button>
    </form>
    <ResultPanel :status="status" :data="result.data" empty-hint="Clique em Buscar lançamentos">
      <template #preview>
        <div v-for="(item, i) in items" :key="i">
          <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" />
        </div>
      </template>
    </ResultPanel>
  </section>
</template>
