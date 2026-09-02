<script setup>
import Icon from "./Icon.vue";

defineProps({
  image: { type: String, default: null },
  title: { type: String, required: true },
  subtitle: { type: String, default: "" },
  url: { type: String, default: null },
});
</script>

<template>
  <div class="media-item-row">
    <img v-if="image" :src="image" :alt="title" class="media-item-image">
    <div v-else class="media-item-image"></div>
    <div class="media-item-info">
      <div class="media-item-title">{{ title }}</div>
      <div v-if="subtitle" class="media-item-subtitle">{{ subtitle }}</div>
    </div>
    <a v-if="url" :href="url" target="_blank" rel="noopener" class="media-item-link" aria-label="Abrir no Spotify">
      <Icon name="external-link" :size="16" />
    </a>
  </div>
</template>
