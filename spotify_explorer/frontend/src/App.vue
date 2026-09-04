<script setup>
import { onMounted, reactive, ref, watch } from "vue";
import { fetchJSON } from "./composables/useApi.js";
import { useAuthStatus } from "./composables/useAuthStatus.js";
import { useTabNavigation } from "./composables/useTabNavigation.js";
import AppSidebar from "./components/AppSidebar.vue";
import NowPlayingModal from "./components/NowPlayingModal.vue";
import SearchTab from "./tabs/SearchTab.vue";
import TrackTab from "./tabs/TrackTab.vue";
import ArtistTab from "./tabs/ArtistTab.vue";
import RecommendationsTab from "./tabs/RecommendationsTab.vue";
import MeusDadosTab from "./tabs/MeusDadosTab.vue";
import AlbumTab from "./tabs/AlbumTab.vue";
import PlaylistTab from "./tabs/PlaylistTab.vue";
import NewReleasesTab from "./tabs/NewReleasesTab.vue";
import PlayerTab from "./tabs/PlayerTab.vue";
import FollowingTab from "./tabs/FollowingTab.vue";
import MyPlaylistsTab from "./tabs/MyPlaylistsTab.vue";

const tabs = [
  { id: "search", label: "Search", icon: "search", component: SearchTab },
  { id: "track", label: "Track & Audio", icon: "disc", component: TrackTab },
  { id: "artist", label: "Artist", icon: "mic", component: ArtistTab },
  { id: "album", label: "Album", icon: "album", component: AlbumTab },
  { id: "playlist", label: "Playlist", icon: "playlist", component: PlaylistTab },
  { id: "new-releases", label: "New Releases", icon: "new-releases", component: NewReleasesTab },
  { id: "recommendations", label: "Recommendations", icon: "sparkles", component: RecommendationsTab },
  { id: "me", label: "Meus dados", icon: "heart", component: MeusDadosTab },
  { id: "player", label: "Player", icon: "player", component: PlayerTab },
  { id: "following", label: "Seguindo", icon: "following", component: FollowingTab },
  { id: "my-playlists", label: "Minhas Playlists", icon: "folder", component: MyPlaylistsTab },
];

const activeTab = ref("search");
const config = reactive({ missingCredentials: false });
const authError = ref(new URLSearchParams(window.location.search).get("auth_error"));
const { state: authState, refresh: refreshAuthStatus } = useAuthStatus();
const { pending } = useTabNavigation();

watch(pending, (nav) => {
  if (nav) activeTab.value = nav.tab;
});

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

    <NowPlayingModal />
  </div>
</template>
