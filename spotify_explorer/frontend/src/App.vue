<script setup>
import { onMounted, reactive, ref } from "vue";
import { fetchJSON } from "./composables/useApi.js";
import SearchTab from "./tabs/SearchTab.vue";
import TrackTab from "./tabs/TrackTab.vue";
import ArtistTab from "./tabs/ArtistTab.vue";
import RecommendationsTab from "./tabs/RecommendationsTab.vue";
import MeusDadosTab from "./tabs/MeusDadosTab.vue";
import { useAuthStatus } from "./composables/useAuthStatus.js";

const tabs = [
  { id: "search", label: "Search", component: SearchTab },
  { id: "track", label: "Track & Audio", component: TrackTab },
  { id: "artist", label: "Artist", component: ArtistTab },
  { id: "recommendations", label: "Recommendations", component: RecommendationsTab },
  { id: "me", label: "Meus dados", component: MeusDadosTab },
];

const activeTab = ref("search");
const config = reactive({ missingCredentials: false });
const authError = ref(new URLSearchParams(window.location.search).get("auth_error"));
const { state: authState, refresh: refreshAuthStatus } = useAuthStatus();

onMounted(async () => {
  const result = await fetchJSON("/api/config");
  if (result.ok) {
    config.missingCredentials = Boolean(result.data.missing_credentials);
  }
  refreshAuthStatus();
});
</script>

<template>
  <header>
    <h1>Spotify API Explorer</h1>
    <div id="user-status">{{ authState.loggedIn ? (authState.profile.display_name || authState.profile.id) : "" }}</div>
  </header>

  <div v-if="config.missingCredentials" class="banner banner-error">
    SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET não configurados. Copie
    <code>.env.example</code> para <code>.env</code> e preencha com um app criado no
    <a href="https://developer.spotify.com/dashboard" target="_blank" rel="noopener">Spotify Developer Dashboard</a>.
  </div>

  <div v-if="authError" class="banner banner-error">Erro no login: {{ authError }}</div>

  <nav class="tabs">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      class="tab-button"
      :class="{ active: activeTab === tab.id }"
      @click="activeTab = tab.id"
    >
      {{ tab.label }}
    </button>
  </nav>

  <KeepAlive>
    <component :is="tabs.find((t) => t.id === activeTab).component" />
  </KeepAlive>
</template>
