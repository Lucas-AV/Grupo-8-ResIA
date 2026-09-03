<script setup>
import { computed, reactive } from "vue";
import { fetchJSON } from "../composables/useApi.js";
import { useAuthStatus } from "../composables/useAuthStatus.js";
import { trackSummary } from "../utils/spotifyShapes.js";
import ResultPanel from "../components/ResultPanel.vue";
import TrackPreview from "../components/previews/TrackPreview.vue";
import MediaItemRow from "../components/MediaItemRow.vue";

const { state: authState } = useAuthStatus();
const status = reactive({ text: "", className: "status", loading: false });
const result = reactive({ data: null });

const nowPlaying = computed(() => result.data?.player?.item ?? null);
const isPlaying = computed(() => result.data?.player?.is_playing ?? false);

const queueItems = computed(() => {
  const items = result.data?.queue?.queue;
  if (!Array.isArray(items)) return [];
  return items.map(trackSummary).filter((item) => item !== null);
});

function formatDuration(ms) {
  if (!ms) return "";
  const totalSeconds = Math.round(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

async function fetchPlayer() {
  status.loading = true;
  status.text = "Carregando...";
  status.className = "status";

  const [player, queue] = await Promise.all([
    fetchJSON("/api/me/player"),
    fetchJSON("/api/me/player/queue"),
  ]);

  status.loading = false;
  const allOk = player.ok && queue.ok;
  const statuses = [player, queue]
    .map((r) => (r.status === 0 ? "erro de rede" : r.status))
    .join(", ");
  status.text = `HTTP ${statuses}`;
  status.className = "status " + (allOk ? "status-ok" : "status-error");
  result.data = { player: player.data, queue: queue.data };
}

async function callControl(action, params = {}) {
  const query = new URLSearchParams(params).toString();
  const url = query ? `/api/me/player/${action}?${query}` : `/api/me/player/${action}`;
  await fetchJSON(url, { method: "POST" });
  await fetchPlayer();
}

function togglePlayPause() {
  callControl(isPlaying.value ? "pause" : "play");
}

const REPEAT_STATES = ["off", "context", "track"];

function cycleRepeat() {
  const current = result.data.player.repeat_state;
  const currentIndex = REPEAT_STATES.indexOf(current);
  const next = REPEAT_STATES[(currentIndex + 1) % REPEAT_STATES.length];
  callControl("repeat", { state: next });
}

const relatedPlaylist = reactive({ status: "", data: null, error: null });

async function generateRelatedPlaylist() {
  relatedPlaylist.status = "loading";
  relatedPlaylist.data = null;
  relatedPlaylist.error = null;

  const outcome = await fetchJSON("/api/me/playlists/related", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ track_id: nowPlaying.value.id, track_name: nowPlaying.value.name }),
  });

  if (outcome.ok) {
    relatedPlaylist.status = "ok";
    relatedPlaylist.data = outcome.data;
  } else {
    relatedPlaylist.status = "error";
    relatedPlaylist.error = outcome.data;
  }
}
</script>

<template>
  <section>
    <h2>Player</h2>
    <div v-if="!authState.loggedIn">
      <p>Nenhum usuário conectado.</p>
      <a class="btn" href="/login">Conectar Spotify</a>
    </div>
    <div v-else>
      <button type="button" class="btn" @click="fetchPlayer">Atualizar</button>
      <button type="button" class="btn btn-secondary" @click="callControl('previous')">⏮ Anterior</button>
      <button type="button" class="btn btn-secondary" @click="togglePlayPause">
        {{ isPlaying ? "⏸ Pausar" : "▶ Tocar" }}
      </button>
      <button type="button" class="btn btn-secondary" @click="callControl('next')">⏭ Próxima</button>
      <ResultPanel
        :status="status"
        :data="result.data"
        empty-hint="Clique em Atualizar pra ver o que está tocando"
      >
        <template #preview>
          <div v-if="nowPlaying">
            <TrackPreview :track="nowPlaying" />
            <button
              type="button"
              class="btn"
              :disabled="relatedPlaylist.status === 'loading'"
              @click="generateRelatedPlaylist"
            >
              Gerar playlist relacionada
            </button>
            <p v-if="relatedPlaylist.status === 'ok'">
              Playlist criada — {{ relatedPlaylist.data.added_tracks }} faixas.
              <a :href="relatedPlaylist.data.playlist.external_urls.spotify" target="_blank" rel="noopener">
                Abrir no Spotify
              </a>
            </p>
            <p v-else-if="relatedPlaylist.status === 'error'" class="status status-error">
              Erro ({{ relatedPlaylist.error?.step }}): {{ JSON.stringify(relatedPlaylist.error?.error) }}
            </p>
            <div class="audio-feature-bar">
              <span>Progresso</span>
              <div class="audio-feature-track">
                <div
                  class="audio-feature-fill"
                  :style="{ width: `${(result.data.player.progress_ms / nowPlaying.duration_ms) * 100}%` }"
                ></div>
              </div>
              <span>
                {{ formatDuration(result.data.player.progress_ms) }} /
                {{ formatDuration(nowPlaying.duration_ms) }}
              </span>
            </div>
            <div class="audio-feature-bar">
              <span>Seek</span>
              <input
                type="range"
                min="0"
                :max="nowPlaying.duration_ms"
                :value="result.data.player.progress_ms"
                @change="callControl('seek', { position_ms: $event.target.value })"
              >
            </div>
            <div v-if="result.data.player.device" class="audio-feature-bar">
              <span>Volume</span>
              <input
                type="range"
                min="0"
                max="100"
                :value="result.data.player.device.volume_percent"
                @change="callControl('volume', { volume_percent: $event.target.value })"
              >
            </div>
            <p v-if="result.data.player.device">
              Dispositivo: {{ result.data.player.device.name }} ({{ result.data.player.device.type }})
              — volume {{ result.data.player.device.volume_percent }}%
            </p>
            <button
              type="button"
              class="btn btn-secondary"
              @click="callControl('shuffle', { state: !result.data.player.shuffle_state })"
            >
              Shuffle: {{ result.data.player.shuffle_state ? "ligado" : "desligado" }}
            </button>
            <button type="button" class="btn btn-secondary" @click="cycleRepeat">
              Repeat: {{ result.data.player.repeat_state }}
            </button>
          </div>
          <p v-else>Nada tocando no momento.</p>
          <div v-if="queueItems.length">
            <h3>Fila</h3>
            <div v-for="(item, i) in queueItems" :key="i">
              <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" :url="item.url" :preview-url="item.previewUrl" />
            </div>
          </div>
        </template>
      </ResultPanel>
    </div>
  </section>
</template>
