import { reactive } from "vue";
import { fetchJSON } from "./useApi.js";

const state = reactive({ loggedIn: false, profile: null });

async function refresh() {
  const result = await fetchJSON("/api/me");

  if (!result.ok) {
    state.loggedIn = false;
    state.profile = null;
    return;
  }

  state.loggedIn = true;
  state.profile = result.data;
}

export function useAuthStatus() {
  return { state, refresh };
}
