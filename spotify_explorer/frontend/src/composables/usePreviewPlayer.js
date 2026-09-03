import { ref } from "vue";

const audio = new Audio();
const playingUrl = ref(null);

audio.addEventListener("ended", () => {
  playingUrl.value = null;
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
    audio.play().catch(() => {});
    playingUrl.value = url;
  }

  return { playingUrl, toggle };
}
