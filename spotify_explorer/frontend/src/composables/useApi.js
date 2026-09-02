import { reactive } from "vue";

export async function fetchJSON(url, options = {}) {
  let response;
  try {
    response = await fetch(url, options);
  } catch (err) {
    return { ok: false, status: 0, data: null, error: String(err) };
  }

  try {
    const data = await response.json();
    return { ok: response.ok, status: response.status, data, error: null };
  } catch (err) {
    return {
      ok: false,
      status: response.status,
      data: null,
      error: `Resposta HTTP ${response.status} não é JSON válido: ${err}`,
    };
  }
}

export function useApi() {
  const status = reactive({ text: "", className: "status", loading: false });

  async function call(url, options = {}) {
    status.loading = true;
    status.text = "Carregando...";
    status.className = "status";

    const result = await fetchJSON(url, options);

    status.loading = false;
    if (result.status === 0) {
      status.text = "Erro de rede";
    } else if (result.error) {
      status.text = result.error;
    } else {
      status.text = `HTTP ${result.status}`;
    }
    status.className = "status " + (result.ok ? "status-ok" : "status-error");

    return result;
  }

  return { status, call };
}
