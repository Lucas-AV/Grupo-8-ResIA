import { ref } from "vue";

function readStorage(key) {
  try {
    return JSON.parse(localStorage.getItem(key) || "[]");
  } catch {
    return [];
  }
}

function writeStorage(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // localStorage indisponível (modo privado, cota excedida, etc.) — ignora
  }
}

export function useHistory(key, limit = 10) {
  const storageKey = `spotify-explorer:history:${key}`;
  const items = ref(readStorage(storageKey));

  function add(value) {
    if (!value) return;
    items.value = [value, ...items.value.filter((v) => v !== value)].slice(0, limit);
    writeStorage(storageKey, items.value);
  }

  return { items, add };
}
