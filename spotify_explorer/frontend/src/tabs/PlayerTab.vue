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
      <ResultPanel
        :status="status"
        :data="result.data"
        empty-hint="Clique em Atualizar pra ver o que está tocando"
      >
        <template #preview>
          <div v-if="nowPlaying">
            <TrackPreview :track="nowPlaying" />
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
            <p v-if="result.data.player.device">
              Dispositivo: {{ result.data.player.device.name }} ({{ result.data.player.device.type }})
              — volume {{ result.data.player.device.volume_percent }}%
            </p>
            <p>
              Shuffle: {{ result.data.player.shuffle_state ? "ligado" : "desligado" }}
              — Repeat: {{ result.data.player.repeat_state }}
            </p>
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
