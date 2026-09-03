<script setup>
import { computed } from "vue";
import { albumSummary } from "../../utils/spotifyShapes.js";
import Icon from "../Icon.vue";

const props = defineProps({
  album: { type: Object, default: null },
});

const summary = computed(() => albumSummary(props.album));
</script>

<template>
  <div v-if="summary" class="preview-card">
    <img v-if="summary.image" :src="summary.image" :alt="summary.title" class="preview-image">
    <div>
      <div class="preview-title">{{ summary.title }}</div>
      <div class="preview-subtitle">{{ summary.subtitle }}</div>
      <div v-if="album.release_date" class="preview-subtitle">{{ album.release_date }}</div>
      <div v-if="album.total_tracks" class="preview-subtitle">{{ album.total_tracks }} faixas</div>
      <a v-if="summary.url" :href="summary.url" target="_blank" rel="noopener" class="preview-spotify-link">
        <Icon name="external-link" :size="14" />
        Abrir no Spotify
      </a>
    </div>
  </div>
</template>
