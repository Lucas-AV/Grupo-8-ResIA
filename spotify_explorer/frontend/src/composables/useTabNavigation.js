import { onMounted, ref, watch } from "vue";

const pending = ref(null); // { tab: string, id: string } | null

export function useTabNavigation() {
  function goTo(tab, id) {
    pending.value = { tab, id };
  }

  function consume(forTab) {
    if (pending.value?.tab !== forTab) return null;
    const id = pending.value.id;
    pending.value = null;
    return id;
  }

  return { pending, goTo, consume };
}

export function useNavigationTarget(tabId, onId) {
  const { pending, consume } = useTabNavigation();

  function applyPending() {
    const id = consume(tabId);
    if (id) onId(id);
  }

  onMounted(applyPending);
  watch(pending, applyPending);
}
