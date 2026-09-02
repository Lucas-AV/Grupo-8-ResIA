<script setup>
import { computed } from "vue";
import { trackSummary } from "../../utils/spotifyShapes.js";

const props = defineProps({
  track: { type: Object, default: null },
  audioFeatures: { type: Object, default: null },
});

const summary = computed(() => trackSummary(props.track));

const hasFeatures = computed(
  () => props.audioFeatures && typeof props.audioFeatures.danceability === "number"
);

const features = [
  { key: "danceability", label: "Danceability" },
  { key: "energy", label: "Energy" },
  { key: "valence", label: "Valence" },
];

function formatDuration(ms) {
  if (!ms) return "";
  const totalSeconds = Math.round(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}
</script>

<template>
  <div v-if="summary" class="preview-card">
    <img v-if="summary.image" :src="summary.image" :alt="summary.title" class="preview-image">
    <div>
      <div class="preview-title">{{ summary.title }}</div>
      <div class="preview-subtitle">{{ summary.subtitle }}</div>
      <div v-if="track.duration_ms" class="preview-subtitle">{{ formatDuration(track.duration_ms) }}</div>
      <div v-if="hasFeatures">
        <div v-for="feature in features" :key="feature.key" class="audio-feature-bar">
          <span>{{ feature.label }}</span>
          <div class="audio-feature-track">
            <div class="audio-feature-fill" :style="{ width: `${audioFeatures[feature.key] * 100}%` }"></div>
          </div>
          <span>{{ Math.round(audioFeatures[feature.key] * 100) }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>
