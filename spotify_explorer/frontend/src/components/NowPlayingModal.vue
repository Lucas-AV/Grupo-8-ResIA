<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useNowPlaying } from "../composables/useNowPlaying.js";
import { usePreviewPlayer } from "../composables/usePreviewPlayer.js";
import Icon from "./Icon.vue";

const { current, close } = useNowPlaying();
const { playingUrl, currentTime, duration, toggle, stop } = usePreviewPlayer();

const hasPreview = computed(() => Boolean(current.value?.previewUrl));
const isPlaying = computed(() => hasPreview.value && playingUrl.value === current.value.previewUrl);

const fakeElapsedMs = ref(0);
let fakeTimer = null;

function startFakeProgress() {
  const totalMs = current.value?.durationMs || 30000;
  fakeTimer = setInterval(() => {
    fakeElapsedMs.value = (fakeElapsedMs.value + 250) % totalMs;
  }, 250);
}

function stopFakeProgress() {
  clearInterval(fakeTimer);
  fakeTimer = null;
  fakeElapsedMs.value = 0;
}

watch(current, (track, previous) => {
  if (previous) stopFakeProgress();
  if (!track) return;
  if (track.previewUrl) {
    toggle(track.previewUrl);
  } else {
    startFakeProgress();
  }
});

function handleClose() {
  stop();
  stopFakeProgress();
  close();
}

function handleKeydown(event) {
  if (event.key === "Escape") handleClose();
}

onMounted(() => window.addEventListener("keydown", handleKeydown));
onUnmounted(() => window.removeEventListener("keydown", handleKeydown));

const progressPercent = computed(() => {
  if (!current.value) return 0;
  if (hasPreview.value) {
    return duration.value ? (currentTime.value / duration.value) * 100 : 0;
  }
  const totalMs = current.value.durationMs || 30000;
  return (fakeElapsedMs.value / totalMs) * 100;
});

function formatSeconds(seconds) {
  if (!seconds || Number.isNaN(seconds)) return "0:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}
</script>

<template>
  <div v-if="current" class="now-playing-backdrop" @click.self="handleClose">
    <div class="now-playing-modal">
      <button type="button" class="now-playing-close" aria-label="Fechar" @click="handleClose">
        <Icon name="close" :size="20" />
      </button>

      <img v-if="current.image" :src="current.image" :alt="current.title" class="now-playing-art">
      <div v-else class="now-playing-art"></div>

      <div class="now-playing-equalizer" :class="{ 'is-playing': isPlaying || !hasPreview }">
        <span v-for="n in 4" :key="n"></span>
      </div>

      <h3 class="now-playing-title">{{ current.title }}</h3>
      <p v-if="current.subtitle" class="now-playing-subtitle">{{ current.subtitle }}</p>

      <div class="now-playing-progress-track">
        <div class="now-playing-progress-fill" :style="{ width: `${progressPercent}%` }"></div>
      </div>
      <p v-if="!hasPreview" class="now-playing-hint">
        Prévia indisponível — visualização ilustrativa (restrição da Spotify desde nov/2024)
      </p>
      <p v-else class="now-playing-hint">
        {{ formatSeconds(currentTime) }} / {{ formatSeconds(duration) }}
      </p>

      <div class="now-playing-controls">
        <button
          v-if="hasPreview"
          type="button"
          class="now-playing-play-btn"
          :aria-label="isPlaying ? 'Pausar' : 'Tocar'"
          @click="toggle(current.previewUrl)"
        >
          <Icon :name="isPlaying ? 'pause' : 'player'" :size="24" />
        </button>
        <a v-if="current.url" :href="current.url" target="_blank" rel="noopener" class="btn btn-secondary">
          <Icon name="external-link" :size="16" />
          Abrir no Spotify
        </a>
      </div>
    </div>
  </div>
</template>
