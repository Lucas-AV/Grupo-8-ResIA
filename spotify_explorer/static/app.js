// spotify_explorer/static/app.js

function initTabs() {
  document.querySelectorAll(".tab-button").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".tab-button").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      button.classList.add("active");
      document.getElementById(button.dataset.tab).classList.add("active");
    });
  });
}

function renderValue(value) {
  if (value === null || value === undefined) {
    return document.createTextNode("null");
  }
  if (Array.isArray(value)) {
    return renderContainer(value, "[", "]");
  }
  if (typeof value === "object") {
    return renderContainer(value, "{", "}");
  }
  return document.createTextNode(JSON.stringify(value));
}

function renderContainer(value, open, close) {
  const entries = Array.isArray(value) ? value.map((v, i) => [i, v]) : Object.entries(value);

  if (entries.length === 0) {
    const span = document.createElement("span");
    span.textContent = open + close;
    return span;
  }

  const details = document.createElement("details");
  details.open = true;
  const summary = document.createElement("summary");
  summary.textContent = `${open} ${entries.length} item(s) ${close}`;
  details.appendChild(summary);

  const list = document.createElement("div");
  list.className = "json-indent";
  entries.forEach(([key, val]) => {
    const row = document.createElement("div");
    const keySpan = document.createElement("span");
    keySpan.className = "json-key";
    keySpan.textContent = `${key}: `;
    row.appendChild(keySpan);
    row.appendChild(renderValue(val));
    list.appendChild(row);
  });
  details.appendChild(list);
  return details;
}

function renderJSON(container, data) {
  container.innerHTML = "";
  container.appendChild(renderValue(data));
}

async function callEndpoint(url, options, resultEl, statusEl) {
  statusEl.textContent = "Carregando...";
  statusEl.className = "status";

  let response;
  try {
    response = await fetch(url, options);
  } catch (err) {
    statusEl.textContent = "Erro de rede";
    statusEl.className = "status status-error";
    resultEl.textContent = String(err);
    return { ok: false, status: 0, data: null };
  }

  statusEl.textContent = `HTTP ${response.status}`;
  statusEl.className = "status " + (response.ok ? "status-ok" : "status-error");

  try {
    const data = await response.json();
    renderJSON(resultEl, data);
    return { ok: response.ok, status: response.status, data };
  } catch (err) {
    statusEl.className = "status status-error";
    resultEl.textContent = `Resposta HTTP ${response.status} não é JSON válido: ${err}`;
    return { ok: false, status: response.status, data: null };
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
});
