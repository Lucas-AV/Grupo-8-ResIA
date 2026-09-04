import { ref } from "vue";

const current = ref(null); // { image, title, subtitle, url, previewUrl, durationMs } | null

export function useNowPlaying() {
  function open(track) {
    current.value = track;
  }

  function close() {
    current.value = null;
  }

  return { current, open, close };
}
