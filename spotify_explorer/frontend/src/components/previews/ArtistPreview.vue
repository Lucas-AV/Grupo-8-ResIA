<script setup>
import { computed } from "vue";
import { artistSummary } from "../../utils/spotifyShapes.js";

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
    </div>
  </div>
</template>
