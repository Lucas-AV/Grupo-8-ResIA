<script setup>
import { computed, reactive, ref } from "vue";
import { useApi } from "../composables/useApi.js";
import { useAuthStatus } from "../composables/useAuthStatus.js";
import { useTabNavigation } from "../composables/useTabNavigation.js";
import { artistSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const { state: authState } = useAuthStatus();
const { goTo } = useTabNavigation();
const limit = ref(20);
const { status, call } = useApi();
const result = reactive({ data: null });

const items = computed(() => {
  const raw = result.data?.artists?.items;
  if (!Array.isArray(raw)) return [];
  return raw
    .map((artist) => {
      const summary = artistSummary(artist);
      return summary ? { id: artist.id, ...summary } : null;
    })
    .filter((item) => item !== null);
});

async function fetchFollowing() {
  const { data } = await call(`/api/me/following?limit=${Number(limit.value)}`);
  result.data = data;
}
</script>

<template>
  <section>
    <h2>Seguindo</h2>
    <div v-if="!authState.loggedIn">
      <p>Nenhum usuário conectado.</p>
      <a class="btn" href="/login">Conectar Spotify</a>
    </div>
    <div v-else>
      <form @submit.prevent="fetchFollowing">
        <label>Limit <input type="number" v-model.number="limit" min="1" max="50"></label>
        <button type="submit" class="btn">Buscar artistas seguidos</button>
      </form>
      <ResultPanel
        :status="status"
        :data="result.data"
        empty-hint="Clique em Buscar pra ver os artistas que você segue"
      >
        <template #preview>
          <button
            v-for="(item, i) in items"
            :key="i"
            type="button"
            class="media-item-clickable"
            @click="goTo('artist', item.id)"
          >
            <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" />
          </button>
        </template>
      </ResultPanel>
    </div>
  </section>
</template>
