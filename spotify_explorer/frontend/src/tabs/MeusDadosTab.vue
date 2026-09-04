<script setup>
import { computed, reactive } from "vue";
import { useApi } from "../composables/useApi.js";
import { useAuthStatus } from "../composables/useAuthStatus.js";
import { useNowPlaying } from "../composables/useNowPlaying.js";
import { trackSummary, artistSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const { state: authState } = useAuthStatus();
const { open } = useNowPlaying();

const timeRange = reactive({ value: "medium_term" });
const topTarget = reactive({ value: "tracks" });

const top = useApi();
const topResult = reactive({ data: null });

const saved = useApi();
const savedResult = reactive({ data: null });

const recentlyPlayed = useApi();
const recentlyPlayedResult = reactive({ data: null });

const topItems = computed(() => {
  if (!topResult.data?.items) return [];
  const summarize = topTarget.value === "artists" ? artistSummary : trackSummary;
  return topResult.data.items.map(summarize).filter((item) => item !== null);
});

const savedItems = computed(() => {
  if (!savedResult.data?.items) return [];
  return savedResult.data.items.map((item) => trackSummary(item.track)).filter((item) => item !== null);
});

const recentlyPlayedItems = computed(() => {
  if (!recentlyPlayedResult.data?.items) return [];
  return recentlyPlayedResult.data.items.map((item) => trackSummary(item.track)).filter((item) => item !== null);
});

async function fetchTop(target) {
  topTarget.value = target;
  const path = target === "artists" ? "/api/me/top/artists" : "/api/me/top/tracks";
  const { data } = await top.call(`${path}?time_range=${timeRange.value}`);
  if (target === topTarget.value) {
    topResult.data = data;
  }
}

async function fetchSaved() {
  const { data } = await saved.call("/api/me/tracks");
  savedResult.data = data;
}

async function fetchRecentlyPlayed() {
  const { data } = await recentlyPlayed.call("/api/me/player/recently-played?limit=50");
  recentlyPlayedResult.data = data;
}
</script>

<template>
  <section>
    <h2>Meus dados</h2>
    <div v-if="!authState.loggedIn">
      <p>Nenhum usuário conectado.</p>
      <a class="btn" href="/login">Conectar Spotify</a>
    </div>
    <div v-else>
      <p>Logado como: {{ authState.profile.display_name || authState.profile.id }}</p>

      <fieldset>
        <legend>Top tracks / artists</legend>
        <form @submit.prevent>
          <label>Time range
            <select v-model="timeRange.value">
              <option value="short_term">short_term (~4 semanas)</option>
              <option value="medium_term">medium_term (~6 meses)</option>
              <option value="long_term">long_term (vários anos)</option>
            </select>
          </label>
          <button type="button" class="btn" @click="fetchTop('tracks')">Top tracks</button>
          <button type="button" class="btn" @click="fetchTop('artists')">Top artists</button>
        </form>
        <ResultPanel :status="top.status" :data="topResult.data" empty-hint="Clique em Top tracks ou Top artists">
          <template #preview>
            <div v-for="(item, i) in topItems" :key="i">
              <button v-if="topTarget.value === 'tracks'" type="button" class="media-item-clickable" @click="open(item)">
                <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" />
              </button>
              <MediaItemRow v-else :image="item.image" :title="item.title" :subtitle="item.subtitle" />
            </div>
          </template>
        </ResultPanel>
      </fieldset>

      <fieldset>
        <legend>Faixas curtidas</legend>
        <button type="button" class="btn" @click="fetchSaved">Buscar curtidas</button>
        <ResultPanel :status="saved.status" :data="savedResult.data" empty-hint="Clique em Buscar curtidas">
          <template #preview>
            <div v-for="(item, i) in savedItems" :key="i">
              <button type="button" class="media-item-clickable" @click="open(item)">
                <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" />
              </button>
            </div>
          </template>
        </ResultPanel>
      </fieldset>

      <fieldset>
        <legend>Tocadas recentemente</legend>
        <button type="button" class="btn" @click="fetchRecentlyPlayed">Buscar recentes (máx. 50)</button>
        <ResultPanel
          :status="recentlyPlayed.status"
          :data="recentlyPlayedResult.data"
          empty-hint="Clique em Buscar recentes"
        >
          <template #preview>
            <div v-for="(item, i) in recentlyPlayedItems" :key="i">
              <button type="button" class="media-item-clickable" @click="open(item)">
                <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" />
              </button>
            </div>
          </template>
        </ResultPanel>
      </fieldset>
    </div>
  </section>
</template>
