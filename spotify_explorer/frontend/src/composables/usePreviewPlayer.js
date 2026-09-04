import { ref } from "vue";

const audio = new Audio();
const playingUrl = ref(null);
const currentTime = ref(0);
const duration = ref(0);

audio.addEventListener("ended", () => {
  playingUrl.value = null;
});
audio.addEventListener("timeupdate", () => {
  currentTime.value = audio.currentTime;
});
audio.addEventListener("loadedmetadata", () => {
  duration.value = audio.duration;
});

export function usePreviewPlayer() {
  function toggle(url) {
    if (!url) return;
    if (playingUrl.value === url) {
      audio.pause();
      playingUrl.value = null;
      return;
    }
    audio.src = url;
    currentTime.value = 0;
    audio.play().catch(() => {});
    playingUrl.value = url;
  }

  function stop() {
    audio.pause();
    playingUrl.value = null;
  }

  return { playingUrl, currentTime, duration, toggle, stop };
}
