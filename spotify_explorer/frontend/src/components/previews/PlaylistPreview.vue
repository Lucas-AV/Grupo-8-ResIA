<script setup>
import { computed } from "vue";
import { playlistSummary } from "../../utils/spotifyShapes.js";
import Icon from "../Icon.vue";

const props = defineProps({
  playlist: { type: Object, default: null },
});

const summary = computed(() => playlistSummary(props.playlist));
</script>

<template>
  <div v-if="summary" class="preview-card">
    <img v-if="summary.image" :src="summary.image" :alt="summary.title" class="preview-image">
    <div>
      <div class="preview-title">{{ summary.title }}</div>
      <div class="preview-subtitle">{{ summary.subtitle }}</div>
      <div v-if="playlist.description" class="preview-subtitle">{{ playlist.description }}</div>
      <div v-if="(playlist.items?.total ?? playlist.tracks?.total) != null" class="preview-subtitle">
        {{ playlist.items?.total ?? playlist.tracks?.total }} faixas
      </div>
      <div v-else class="preview-subtitle">Faixas: indisponível (restrição da Spotify)</div>
      <a v-if="summary.url" :href="summary.url" target="_blank" rel="noopener" class="preview-spotify-link">
        <Icon name="external-link" :size="14" />
        Abrir no Spotify
      </a>
    </div>
  </div>
</template>
