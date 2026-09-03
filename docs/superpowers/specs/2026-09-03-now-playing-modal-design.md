# Spotify API Explorer — Modal "Tocando agora" pro clique em faixas

**Data:** 2026-09-03
**Branch:** a partir da `feature/spotify-explorer-qr-login` (preview player e Fase 2 já mergeados)

## Objetivo

Hoje, clicar numa linha de faixa (`MediaItemRow`) não faz nada além do
botão de play inline (30s de prévia) e do ícone de link externo (abre
o Spotify numa aba nova — a única forma "grande" de ver a faixa hoje).
Queremos que clicar na linha inteira abra um modal "tocando agora" —
capa grande, título, animação de equalizador, barra de progresso,
play/pause — dando a sensação de um player de verdade, sem sair do
app. O link "Abrir no Spotify" continua existindo, só que dentro do
modal, não mais na linha.

**Ressalva conhecida (mesma da feature de preview, já documentada em
[`2026-09-03-spotify-preview-player-design.md`](2026-09-03-spotify-preview-player-design.md)):**
desde nov/2024 `preview_url` vem `null` pra apps novos. O modal precisa
funcionar bem mesmo sem áudio real — é o caso comum, não a exceção.

## Escopo

Só as linhas de **faixa** renderizadas por `MediaItemRow`. Artistas,
álbuns e playlists (`ArtistTab` related-artists, `NewReleasesTab`,
`FollowingTab`, `MyPlaylistsTab`) continuam exatamente como estão —
`FollowingTab`/`MyPlaylistsTab` já têm seu próprio clique (navegação
via `goTo`, ticket da Fase 2), e não faz sentido abrir um "tocando
agora" pra um artista ou álbum.

A tela de detalhe da aba **Track & Audio** (`TrackTab` → `TrackPreview`)
fica fora de escopo — já é uma visão completa dedicada a uma faixa, não
uma lista pra clicar. Idem o card "tocando agora" real do `PlayerTab`
(estado real de reprodução do usuário) — só a fila abaixo dele (que usa
`MediaItemRow`) entra no escopo.

10 pontos de uso de `MediaItemRow` hoje; desses, **8 são faixas** e
ganham o clique novo:

| Arquivo | Linha (pré-mudança) | É faixa? |
|---|---|---|
| `SearchTab.vue` | resultado de busca (track/artist/album) | Só quando `submittedType === 'track'` |
| `RecommendationsTab.vue` | resultado de `/recommendations` | Sim, sempre |
| `ArtistTab.vue` | top tracks | Sim, sempre |
| `ArtistTab.vue` | related artists | Não — sem mudança |
| `AlbumTab.vue` | faixas do álbum | Sim, sempre |
| `PlaylistTab.vue` | faixas da playlist | Sim, sempre |
| `MeusDadosTab.vue` | top tracks/artists | Só quando `topTarget === 'tracks'` |
| `MeusDadosTab.vue` | faixas curtidas | Sim, sempre |
| `MeusDadosTab.vue` | tocadas recentemente | Sim, sempre |
| `PlayerTab.vue` | fila (queue) | Sim, sempre |

## `useNowPlaying.js` — novo composable

Mesmo padrão module-scoped "singleton" de `useTabNavigation.js` — um
único estado compartilhado por toda a página, sem Vuex/Pinia:

```js
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
```

## `usePreviewPlayer.js` — expor progresso real

Hoje só expõe `playingUrl`/`toggle`. O modal precisa de posição/duração
reais quando existe `preview_url`, pra barra de progresso não ser
totalmente falsa nesse caso:

```js
import { ref } from "vue";

const audio = new Audio();
const playingUrl = ref(null);
const currentTime = ref(0);
const duration = ref(0);

audio.addEventListener("ended", () => {
  playingUrl.value = null;
});
audio.addEventListener("timeupdate", () => {
  currentTime.value = audio.currentTime;
});
audio.addEventListener("loadedmetadata", () => {
  duration.value = audio.duration;
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
    currentTime.value = 0;
    audio.play().catch(() => {});
    playingUrl.value = url;
  }

  function stop() {
    audio.pause();
    playingUrl.value = null;
  }

  return { playingUrl, currentTime, duration, toggle, stop };
}
```

`stop()` é novo — usado pelo modal ao fechar, pra prévia não continuar
tocando com o modal escondido (diferente do preview inline de hoje, que
deixa tocando ao trocar de aba de propósito; aqui o modal fechar é uma
ação explícita de "parar de ver/ouvir isso").

## `NowPlayingModal.vue` — novo componente

Montado uma vez em `App.vue`, fora da `KeepAlive` das tabs (sobrepõe
qualquer aba). Renderiza `null` quando `current` é `null`.

```vue
<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useNowPlaying } from "../composables/useNowPlaying.js";
import { usePreviewPlayer } from "../composables/usePreviewPlayer.js";
import Icon from "./Icon.vue";

const { current, close } = useNowPlaying();
const { playingUrl, currentTime, duration, toggle, stop } = usePreviewPlayer();

const hasPreview = computed(() => Boolean(current.value?.previewUrl));
const isPlaying = computed(() => hasPreview.value && playingUrl.value === current.value.previewUrl);

// Progresso falso (sem preview_url): avança sozinho em loop, só visual.
const fakeElapsedMs = ref(0);
let fakeTimer = null;

function startFakeProgress() {
  const totalMs = current.value?.durationMs || 30000;
  fakeTimer = setInterval(() => {
    fakeElapsedMs.value = (fakeElapsedMs.value + 250) % totalMs;
  }, 250);
}

function stopFakeProgress() {
  clearInterval(fakeTimer);
  fakeTimer = null;
  fakeElapsedMs.value = 0;
}

watch(current, (track, previous) => {
  if (previous) stopFakeProgress();
  if (!track) return;
  if (track.previewUrl) {
    toggle(track.previewUrl);
  } else {
    startFakeProgress();
  }
});

function handleClose() {
  stop();
  stopFakeProgress();
  close();
}

function handleKeydown(event) {
  if (event.key === "Escape") handleClose();
}

onMounted(() => window.addEventListener("keydown", handleKeydown));
onUnmounted(() => window.removeEventListener("keydown", handleKeydown));

const progressPercent = computed(() => {
  if (!current.value) return 0;
  if (hasPreview.value) {
    return duration.value ? (currentTime.value / duration.value) * 100 : 0;
  }
  const totalMs = current.value.durationMs || 30000;
  return (fakeElapsedMs.value / totalMs) * 100;
});

function formatSeconds(seconds) {
  if (!seconds || Number.isNaN(seconds)) return "0:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}
</script>

<template>
  <div v-if="current" class="now-playing-backdrop" @click.self="handleClose">
    <div class="now-playing-modal">
      <button type="button" class="now-playing-close" aria-label="Fechar" @click="handleClose">
        <Icon name="close" :size="20" />
      </button>

      <img v-if="current.image" :src="current.image" :alt="current.title" class="now-playing-art">
      <div v-else class="now-playing-art now-playing-art-empty"></div>

      <div class="now-playing-equalizer" :class="{ 'is-playing': isPlaying || !hasPreview }">
        <span v-for="n in 4" :key="n"></span>
      </div>

      <h3 class="now-playing-title">{{ current.title }}</h3>
      <p v-if="current.subtitle" class="now-playing-subtitle">{{ current.subtitle }}</p>

      <div class="now-playing-progress-track">
        <div class="now-playing-progress-fill" :style="{ width: `${progressPercent}%` }"></div>
      </div>
      <p v-if="!hasPreview" class="now-playing-hint">
        Prévia indisponível — visualização ilustrativa (restrição da Spotify desde nov/2024)
      </p>
      <p v-else class="now-playing-hint">
        {{ formatSeconds(currentTime) }} / {{ formatSeconds(duration) }}
      </p>

      <div class="now-playing-controls">
        <button
          v-if="hasPreview"
          type="button"
          class="now-playing-play-btn"
          :aria-label="isPlaying ? 'Pausar' : 'Tocar'"
          @click="toggle(current.previewUrl)"
        >
          <Icon :name="isPlaying ? 'pause' : 'player'" :size="24" />
        </button>
        <a v-if="current.url" :href="current.url" target="_blank" rel="noopener" class="btn btn-secondary">
          <Icon name="external-link" :size="16" />
          Abrir no Spotify
        </a>
      </div>
    </div>
  </div>
</template>
```

Notas de comportamento:

- O modal abre já "tocando": o `watch(current, ...)` chama
  `toggle(track.previewUrl)` (ou inicia o progresso falso) assim que
  `current` deixa de ser `null` — não precisa de um segundo clique no
  play depois de abrir. Isso é o pedido original: clicar na faixa já
  mostra ela "tocando", sem passo extra.
- `@click.self` no backdrop fecha só quando o clique é no fundo, não
  quando borbulha de dentro do card.
- Sem `preview_url`: não há botão de play/pause (não existe nada real
  pra tocar/pausar) — só a animação de equalizador rodando sozinha e o
  aviso de prévia indisponível. É a decisão já tomada: abre mesmo assim,
  sem áudio, com aviso discreto.
- Trocar de faixa com o modal já aberto (clicar em outra linha atrás,
  cenário raro mas possível se o modal não bloquear scroll) — o
  `watch(current, ...)` já para o progresso falso anterior antes de
  iniciar o novo; `toggle()` do `usePreviewPlayer` já troca a URL do
  `<audio>` sozinho.

## `Icon.vue` — novo ícone `close`

```js
close: "M4.3 4.3a1 1 0 011.4 0L10 8.6l4.3-4.3a1 1 0 111.4 1.4L11.4 10l4.3 4.3a1 1 0 01-1.4 1.4L10 11.4l-4.3 4.3a1 1 0 01-1.4-1.4L8.6 10 4.3 5.7a1 1 0 010-1.4z",
```

## `MediaItemRow.vue` — remove o play inline e o link externo

Esses dois botões saem da linha (viram ações do modal). A linha volta a
ser só imagem + info, exatamente como era antes da feature de preview —
`previewUrl`/`url` continuam sendo props (usadas agora só pra montar o
objeto passado a `open()` no componente pai), mas não renderizam nada
aqui:

```vue
<script setup>
defineProps({
  image: { type: String, default: null },
  title: { type: String, required: true },
  subtitle: { type: String, default: "" },
});
</script>

<template>
  <div class="media-item-row">
    <img v-if="image" :src="image" :alt="title" class="media-item-image">
    <div v-else class="media-item-image"></div>
    <div class="media-item-info">
      <div class="media-item-title">{{ title }}</div>
      <div v-if="subtitle" class="media-item-subtitle">{{ subtitle }}</div>
    </div>
  </div>
</template>
```

`url`/`previewUrl` somem das props porque quem precisa deles agora é o
componente pai (pra montar o objeto do `open()`), não a própria linha —
menos props não usadas é melhor que manter por "compatibilidade".

## `spotifyShapes.js` — `trackSummary()` ganha `durationMs`

```js
export function trackSummary(track) {
  if (!track || !track.name) return null;
  return {
    image: track.album?.images?.[0]?.url ?? null,
    title: track.name,
    subtitle: asArray(track.artists).map((a) => a.name).join(", "),
    url: spotifyUrl(track),
    previewUrl: track.preview_url ?? null,
    durationMs: track.duration_ms ?? null,
  };
}
```

`artistSummary`/`albumSummary`/`playlistSummary` não mudam.

## Tabs — envolver linhas de faixa num botão clicável

Mesmo padrão já usado por `FollowingTab`/`MyPlaylistsTab` pra navegação
(`<button class="media-item-clickable" @click="...">`), trocando
`goTo(...)` por `open(item)`:

```vue
<button
  v-for="(item, i) in items"
  :key="i"
  type="button"
  class="media-item-clickable"
  @click="open(item)"
>
  <MediaItemRow :image="item.image" :title="item.title" :subtitle="item.subtitle" />
</button>
```

Cada arquivo da tabela de escopo importa `useNowPlaying` e troca a
`<div>`/`<div v-for>` que envolve `MediaItemRow` por esse `<button>`.
Nos dois pontos condicionais:

- `SearchTab.vue`: `v-if="submittedType === 'track'"` decide entre esse
  botão (track) e a `<div>` sem clique de hoje (artist/album).
- `MeusDadosTab.vue` (bloco de top tracks/artists): mesma lógica com
  `topTarget.value === 'tracks'`.

## Estilos — `style.css`

Novo bloco, mesma linguagem visual das outras (`--bg-elevated`,
`--accent`, `--radius-md`):

```css
.now-playing-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.now-playing-modal {
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
  padding: 2rem;
  width: 320px;
  max-width: 90vw;
  text-align: center;
  position: relative;
}

.now-playing-close {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
}

.now-playing-art {
  width: 100%;
  aspect-ratio: 1;
  border-radius: var(--radius-sm);
  object-fit: cover;
  background: var(--bg-elevated-hover);
}

.now-playing-equalizer {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  gap: 4px;
  height: 20px;
  margin: 1rem 0;
}

.now-playing-equalizer span {
  width: 4px;
  height: 6px;
  background: var(--accent);
  border-radius: 2px;
}

.now-playing-equalizer.is-playing span {
  animation: now-playing-bounce 0.8s ease-in-out infinite;
}

.now-playing-equalizer span:nth-child(2) { animation-delay: 0.15s; }
.now-playing-equalizer span:nth-child(3) { animation-delay: 0.3s; }
.now-playing-equalizer span:nth-child(4) { animation-delay: 0.45s; }

@keyframes now-playing-bounce {
  0%, 100% { height: 6px; }
  50% { height: 20px; }
}

.now-playing-title {
  margin: 0.25rem 0 0;
}

.now-playing-subtitle {
  color: var(--text-secondary);
  margin: 0.25rem 0 1rem;
}

.now-playing-progress-track {
  height: 4px;
  background: var(--bg-elevated-hover);
  border-radius: 2px;
  overflow: hidden;
}

.now-playing-progress-fill {
  height: 100%;
  background: var(--accent);
}

.now-playing-hint {
  color: var(--text-muted);
  font-size: 0.8rem;
  margin: 0.5rem 0 1rem;
}

.now-playing-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.now-playing-play-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--accent);
  color: #000;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.now-playing-play-btn:hover {
  background: var(--accent-hover);
}
```

`prefers-reduced-motion` fora de escopo — é uma dev tool interna, não
um produto público; mesmo padrão de acessibilidade "básico, não
exaustivo" já aplicado no resto do app (`aria-label` nos ícones, sem
tratamento de `prefers-reduced-motion` em nenhuma outra animação
existente).

## `App.vue` — montar o modal

```vue
<script setup>
import NowPlayingModal from "./components/NowPlayingModal.vue";
// ...imports existentes
</script>

<template>
  <div class="app-shell">
    <!-- ...existente... -->
    <NowPlayingModal />
  </div>
</template>
```

Fora da `KeepAlive`/`main.app-main`, direto em `app-shell`, pra
sobrepor a sidebar também (o `position: fixed; inset: 0` do backdrop já
cobre a tela inteira independente de onde é montado, mas manter fora da
troca de abas evita qualquer risco de ser desmontado no meio de uma
"reprodução").

## Testes

Sem suíte de testes JS (convenção já estabelecida no projeto). Verificação:
`npm run build` sem erros + revisão manual no navegador — abrir cada
uma das 8 tabelas de escopo, clicar numa faixa, conferir que o modal
abre com e sem `preview_url`, que fechar (X, backdrop, Esc) para o
áudio, e que o botão de play/pause já removido da linha não deixa
"botão fantasma" nenhum pra trás.

## Fora de escopo

- Tocar a faixa de verdade via `/me/player` (like o Player tab já faz
  pro dispositivo ativo do usuário) — o modal é só sobre a
  prévia/simulação de faixas do catálogo, não substitui os controles
  reais de reprodução que já existem no `PlayerTab`.
- `prefers-reduced-motion` (ver nota acima).
- Fila/histórico de faixas "tocadas" dentro do modal (next/previous) —
  o modal é sobre uma faixa por vez, fechando ao trocar; não é um mini
  player persistente.
- Barra de seek arrastável no modal — só play/pause e progresso
  read-only, mesmo espírito de simplicidade do preview inline que ele
  substitui.
</content>
