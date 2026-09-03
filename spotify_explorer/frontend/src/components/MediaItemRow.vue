<script setup>
defineProps({
  image: { type: String, default: null },
  title: { type: String, required: true },
  subtitle: { type: String, default: "" },
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
  </div>
</template>
