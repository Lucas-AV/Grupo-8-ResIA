<script setup>
import { computed } from "vue";
import { trackSummary } from "../../utils/spotifyShapes.js";
import Icon from "../Icon.vue";

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
      <div class="preview-title">
        {{ summary.title }}
        <span v-if="track.explicit" class="preview-explicit-badge">Explicit</span>
      </div>
      <div class="preview-subtitle">{{ summary.subtitle }}</div>
      <div v-if="track.duration_ms" class="preview-subtitle">{{ formatDuration(track.duration_ms) }}</div>
      <a v-if="summary.url" :href="summary.url" target="_blank" rel="noopener" class="preview-spotify-link">
        <Icon name="external-link" :size="14" />
        Abrir no Spotify
      </a>
      <div v-if="typeof track.popularity === 'number'" class="audio-feature-bar">
        <span>Popularidade</span>
        <div class="audio-feature-track">
          <div class="audio-feature-fill" :style="{ width: `${track.popularity}%` }"></div>
        </div>
        <span>{{ track.popularity }}%</span>
      </div>
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
