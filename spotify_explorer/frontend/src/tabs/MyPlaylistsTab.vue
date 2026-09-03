<script setup>
import { computed, reactive, ref } from "vue";
import { useApi } from "../composables/useApi.js";
import { useAuthStatus } from "../composables/useAuthStatus.js";
import { useTabNavigation } from "../composables/useTabNavigation.js";
import { playlistSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const { state: authState } = useAuthStatus();
const { goTo } = useTabNavigation();
const limit = ref(20);
const { status, call } = useApi();
const result = reactive({ data: null });

const items = computed(() => {
  const raw = result.data?.items;
  if (!Array.isArray(raw)) return [];
  return raw
    .map((playlist) => {
      const summary = playlistSummary(playlist);
      if (!summary) return null;
      return {
        id: playlist.id,
        ...summary,
        subtitle: `${summary.subtitle} — ${playlist.public ? "pública" : "privada"}`,
      };
    })
    .filter((item) => item !== null);
});

async function fetchPlaylists() {
  const { data } = await call(`/api/me/playlists?limit=${Number(limit.value)}`);
  result.data = data;
}
</script>

<template>
  <section>
    <h2>Minhas Playlists</h2>
    <div v-if="!authState.loggedIn">
      <p>Nenhum usuário conectado.</p>
      <a class="btn" href="/login">Conectar Spotify</a>
    </div>
    <div v-else>
      <form @submit.prevent="fetchPlaylists">
        <label>Limit <input type="number" v-model.number="limit" min="1" max="50"></label>
        <button type="submit" class="btn">Buscar minhas playlists</button>
      </form>
      <ResultPanel
        :status="status"
        :data="result.data"
        empty-hint="Clique em Buscar pra listar suas playlists"
      >
        <template #preview>
          <button
            v-for="(item, i) in items"
            :key="i"
            type="button"
            class="media-item-clickable"
            @click="goTo('playlist', item.id)"
          >
            <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" />
          </button>
        </template>
      </ResultPanel>
    </div>
  </section>
</template>
