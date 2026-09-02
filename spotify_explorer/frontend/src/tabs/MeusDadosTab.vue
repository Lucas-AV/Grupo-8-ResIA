<script setup>
import { reactive } from "vue";
import { useApi } from "../composables/useApi.js";
import { useAuthStatus } from "../composables/useAuthStatus.js";
import JsonViewer from "../components/JsonViewer.vue";

const { state: authState } = useAuthStatus();

const timeRange = reactive({ value: "medium_term" });

const top = useApi();
const topResult = reactive({ data: null });

const saved = useApi();
const savedResult = reactive({ data: null });

const recentlyPlayed = useApi();
const recentlyPlayedResult = reactive({ data: null });

async function fetchTop(target) {
  const path = target === "artists" ? "/api/me/top/artists" : "/api/me/top/tracks";
  const { data } = await top.call(`${path}?time_range=${timeRange.value}`);
  topResult.data = data;
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
    <div v-if="!authState.loggedIn">
      <p>Nenhum usuário conectado.</p>
      <a class="button" href="/login">Conectar Spotify</a>
    </div>
    <div v-else>
      <p>Logado como: {{ authState.profile.display_name || authState.profile.id }}</p>
      <a class="button" href="/logout">Desconectar</a>

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
          <button type="button" @click="fetchTop('tracks')">Top tracks</button>
          <button type="button" @click="fetchTop('artists')">Top artists</button>
        </form>
        <p :class="top.status.className">{{ top.status.text }}</p>
        <div class="result"><JsonViewer v-if="topResult.data !== null" :data="topResult.data" /></div>
      </fieldset>

      <fieldset>
        <legend>Faixas curtidas</legend>
        <button type="button" @click="fetchSaved">Buscar curtidas</button>
        <p :class="saved.status.className">{{ saved.status.text }}</p>
        <div class="result"><JsonViewer v-if="savedResult.data !== null" :data="savedResult.data" /></div>
      </fieldset>

      <fieldset>
        <legend>Tocadas recentemente</legend>
        <button type="button" @click="fetchRecentlyPlayed">Buscar recentes (máx. 50)</button>
        <p :class="recentlyPlayed.status.className">{{ recentlyPlayed.status.text }}</p>
        <div class="result"><JsonViewer v-if="recentlyPlayedResult.data !== null" :data="recentlyPlayedResult.data" /></div>
      </fieldset>
    </div>
  </section>
</template>
