<script setup>
import { computed } from "vue";
import { artistSummary } from "../../utils/spotifyShapes.js";
import Icon from "../Icon.vue";

const props = defineProps({
  artist: { type: Object, default: null },
});

const summary = computed(() => artistSummary(props.artist));
</script>

<template>
  <div v-if="summary" class="preview-card">
    <img v-if="summary.image" :src="summary.image" :alt="summary.title" class="preview-image">
    <div>
      <div class="preview-title">{{ summary.title }}</div>
      <div class="preview-subtitle">{{ summary.subtitle }}</div>
      <div v-if="artist.genres?.length" class="preview-genres">
        <span v-for="genre in artist.genres" :key="genre" class="preview-genre-chip">{{ genre }}</span>
      </div>
      <a v-if="summary.url" :href="summary.url" target="_blank" rel="noopener" class="preview-spotify-link">
        <Icon name="external-link" :size="14" />
        Abrir no Spotify
      </a>
      <div v-if="typeof artist.popularity === 'number'" class="audio-feature-bar">
        <span>Popularidade</span>
        <div class="audio-feature-track">
          <div class="audio-feature-fill" :style="{ width: `${artist.popularity}%` }"></div>
        </div>
        <span>{{ artist.popularity }}%</span>
      </div>
    </div>
  </div>
</template>
