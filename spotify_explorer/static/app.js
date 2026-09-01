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

function initSearchForm() {
  const form = document.getElementById("search-form");
  const resultEl = document.getElementById("search-result");
  const statusEl = document.getElementById("search-status");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    await callEndpoint(
      "/api/search",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          q: formData.get("q"),
          type: formData.get("type"),
          limit: Number(formData.get("limit")),
        }),
      },
      resultEl,
      statusEl
    );
  });
}

async function fetchJSON(url) {
  const response = await fetch(url);
  let data;
  try {
    data = await response.json();
  } catch (err) {
    data = { error: `Resposta HTTP ${response.status} não é JSON válido: ${err}` };
  }
  return { status: response.status, ok: response.ok, data };
}

function initTrackForm() {
  const form = document.getElementById("track-form");
  const resultEl = document.getElementById("track-result");
  const statusEl = document.getElementById("track-status");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const trackId = new FormData(form).get("track_id");

    statusEl.textContent = "Carregando...";
    statusEl.className = "status";

    try {
      const [track, audioFeatures, audioAnalysis] = await Promise.all([
        fetchJSON(`/api/track/${trackId}`),
        fetchJSON(`/api/audio-features/${trackId}`),
        fetchJSON(`/api/audio-analysis/${trackId}`),
      ]);

      const results = [track, audioFeatures, audioAnalysis];
      const allOk = results.every((r) => r.ok);
      const statuses = results.map((r) => r.status).join(", ");
      statusEl.textContent = `HTTP ${statuses}`;
      statusEl.className = "status " + (allOk ? "status-ok" : "status-error");
      renderJSON(resultEl, {
        track: track.data,
        audio_features: audioFeatures.data,
        audio_analysis: audioAnalysis.data,
      });
    } catch (err) {
      statusEl.textContent = "Erro de rede";
      statusEl.className = "status status-error";
      resultEl.textContent = String(err);
    }
  });
}

function initArtistForm() {
  const form = document.getElementById("artist-form");
  const resultEl = document.getElementById("artist-result");
  const statusEl = document.getElementById("artist-status");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const artistId = new FormData(form).get("artist_id");

    statusEl.textContent = "Carregando...";
    statusEl.className = "status";

    try {
      const [artist, topTracks, albums, relatedArtists] = await Promise.all([
        fetchJSON(`/api/artist/${artistId}`),
        fetchJSON(`/api/artist/${artistId}/top-tracks`),
        fetchJSON(`/api/artist/${artistId}/albums`),
        fetchJSON(`/api/artist/${artistId}/related-artists`),
      ]);

      const results = [artist, topTracks, albums, relatedArtists];
      const allOk = results.every((r) => r.ok);
      const statuses = results.map((r) => r.status).join(", ");
      statusEl.textContent = `HTTP ${statuses}`;
      statusEl.className = "status " + (allOk ? "status-ok" : "status-error");
      renderJSON(resultEl, {
        artist: artist.data,
        top_tracks: topTracks.data,
        albums: albums.data,
        related_artists: relatedArtists.data,
      });
    } catch (err) {
      statusEl.textContent = "Erro de rede";
      statusEl.className = "status status-error";
      resultEl.textContent = String(err);
    }
  });
}

function initRecommendationsForm() {
  const form = document.getElementById("recommendations-form");
  const resultEl = document.getElementById("recommendations-result");
  const statusEl = document.getElementById("recommendations-status");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    const params = new URLSearchParams();
    for (const [key, value] of formData.entries()) {
      if (value) params.set(key, value);
    }
    await callEndpoint(`/api/recommendations?${params}`, {}, resultEl, statusEl);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initSearchForm();
  initTrackForm();
  initArtistForm();
  initRecommendationsForm();
});
