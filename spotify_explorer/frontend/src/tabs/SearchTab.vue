<script setup>
import { computed, reactive, ref } from "vue";
import { useApi } from "../composables/useApi.js";
import { useHistory } from "../composables/useHistory.js";
import { useNowPlaying } from "../composables/useNowPlaying.js";
import { trackSummary, artistSummary, albumSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const form = reactive({ q: "", type: "track", limit: 10 });
const { status, call } = useApi();
const result = reactive({ data: null });
const { items: history, add: addToHistory } = useHistory("search");
const submittedType = ref(form.type);
const { open } = useNowPlaying();

const summaryFn = { track: trackSummary, artist: artistSummary, album: albumSummary };

const items = computed(() => {
  if (!result.data) return [];
  const list = result.data[`${submittedType.value}s`]?.items ?? [];
  const summarize = summaryFn[submittedType.value];
  return list.map(summarize).filter((item) => item !== null);
});

async function onSubmit() {
  submittedType.value = form.type;
  const { data } = await call("/api/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ q: form.q, type: form.type, limit: Number(form.limit) }),
  });
  result.data = data;
  addToHistory(form.q);
}
</script>

<template>
  <section>
    <h2>Search</h2>
    <div v-if="history.length" class="history-chips">
      <button v-for="item in history" :key="item" type="button" class="history-chip" @click="form.q = item">
        {{ item }}
      </button>
    </div>
    <form @submit.prevent="onSubmit">
      <label>Query <input type="text" v-model="form.q" required></label>
      <label>Type
        <select v-model="form.type">
          <option value="track">track</option>
          <option value="artist">artist</option>
          <option value="album">album</option>
        </select>
      </label>
      <label>Limit <input type="number" v-model.number="form.limit" min="1" max="50"></label>
      <button type="submit" class="btn">Buscar</button>
    </form>
    <ResultPanel
      :status="status"
      :data="result.data"
      empty-hint="Digite um termo e escolha o tipo pra buscar no catálogo"
    >
      <template #preview>
        <div v-for="(item, i) in items" :key="i">
          <button v-if="submittedType === 'track'" type="button" class="media-item-clickable" @click="open(item)">
            <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" />
          </button>
          <MediaItemRow v-else :image="item.image" :title="item.title" :subtitle="item.subtitle" />
        </div>
      </template>
    </ResultPanel>
  </section>
</template>
