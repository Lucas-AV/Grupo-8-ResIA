<script setup>
import { onMounted, reactive, ref } from "vue";
import { fetchJSON } from "./composables/useApi.js";
import { useAuthStatus } from "./composables/useAuthStatus.js";
import AppSidebar from "./components/AppSidebar.vue";
import SearchTab from "./tabs/SearchTab.vue";
import TrackTab from "./tabs/TrackTab.vue";
import ArtistTab from "./tabs/ArtistTab.vue";
import RecommendationsTab from "./tabs/RecommendationsTab.vue";
import MeusDadosTab from "./tabs/MeusDadosTab.vue";

const tabs = [
  { id: "search", label: "Search", icon: "search", component: SearchTab },
  { id: "track", label: "Track & Audio", icon: "disc", component: TrackTab },
  { id: "artist", label: "Artist", icon: "mic", component: ArtistTab },
  { id: "recommendations", label: "Recommendations", icon: "sparkles", component: RecommendationsTab },
  { id: "me", label: "Meus dados", icon: "heart", component: MeusDadosTab },
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
  <div class="app-shell">
    <AppSidebar :tabs="tabs" :active-tab="activeTab" :auth-state="authState" @select="activeTab = $event" />

    <main class="app-main">
      <div v-if="config.missingCredentials" class="banner banner-error">
        SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET não configurados. Copie
        <code>.env.example</code> para <code>.env</code> e preencha com um app criado no
        <a href="https://developer.spotify.com/dashboard" target="_blank" rel="noopener">Spotify Developer Dashboard</a>.
      </div>

      <div v-if="authError" class="banner banner-error">Erro no login: {{ authError }}</div>

      <KeepAlive>
        <component :is="tabs.find((t) => t.id === activeTab).component" />
      </KeepAlive>
    </main>
  </div>
</template>
