<script setup>
import Icon from "./Icon.vue";
import { usePreviewPlayer } from "../composables/usePreviewPlayer.js";

defineProps({
  image: { type: String, default: null },
  title: { type: String, required: true },
  subtitle: { type: String, default: "" },
  url: { type: String, default: null },
  previewUrl: { type: String, default: null },
});

const { playingUrl, toggle } = usePreviewPlayer();
</script>

<template>
  <div class="media-item-row">
    <img v-if="image" :src="image" :alt="title" class="media-item-image">
    <div v-else class="media-item-image"></div>
    <div class="media-item-info">
      <div class="media-item-title">{{ title }}</div>
      <div v-if="subtitle" class="media-item-subtitle">{{ subtitle }}</div>
    </div>
    <button
      v-if="previewUrl"
      type="button"
      class="media-item-link"
      :aria-label="playingUrl === previewUrl ? 'Pausar prévia' : 'Tocar prévia (30s)'"
      @click.stop="toggle(previewUrl)"
    >
      <Icon :name="playingUrl === previewUrl ? 'pause' : 'player'" :size="16" />
    </button>
    <a v-if="url" :href="url" target="_blank" rel="noopener" class="media-item-link" aria-label="Abrir no Spotify" @click.stop>
      <Icon name="external-link" :size="16" />
    </a>
  </div>
</template>
