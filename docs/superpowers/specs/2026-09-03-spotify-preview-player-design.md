# Spotify API Explorer — Tocar preview_url (demo de 30s)

**Data:** 2026-09-03
**Branch:** a partir da `main` (Fase 2 e o fix de fev/2026 já mergeados)

## Objetivo

Adicionar um botão de play/pause em toda linha/card de faixa da
ferramenta, tocando o `preview_url` (clipe de 30s em MP3) que a
Spotify já devolve em todo objeto Track — hoje ignorado.

**Ressalva conhecida (não é escopo corrigir, é o que estamos testando
na prática):** desde 27/nov/2024 a Spotify não preenche mais
`preview_url` pra apps novos, mesmo com Extended Quota Mode — o campo
vem `null`. Como esse app foi criado depois disso, é bem provável que
`preview_url` nunca venha preenchido em nenhuma chamada. A feature é
construída mesmo assim: se vier sempre `null`, o botão nunca aparece
em lugar nenhum — isso já é a confirmação prática da restrição, no
mesmo espírito das outras (`audio-features`, `top-tracks`, etc.) já
documentadas no README.

## Estado compartilhado — `usePreviewPlayer.js`

Novo composable, mesmo padrão module-scoped de `useTabNavigation.js`
(um "singleton" reativo, sem Vuex/Pinia): um único `<audio>` real por
página inteira, garantindo que só uma prévia toca por vez em qualquer
lugar do app — clicar em play numa linha para automaticamente
qualquer outra que já estivesse tocando.

```js
import { ref } from "vue";

const audio = new Audio();
const playingUrl = ref(null);

audio.addEventListener("ended", () => {
  playingUrl.value = null;
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
    audio.play();
    playingUrl.value = url;
  }

  return { playingUrl, toggle };
}
```

Sem tratamento de erro além do que já existe naturalmente: se a URL
estiver expirada/inválida, `audio.play()` falha silenciosamente (não
propaga pra UI) — comportamento aceitável numa dev tool, não vale a
complexidade de mostrar esse erro em cada linha.

## `Icon.vue` — novo ícone `pause`

O ícone `player` (triângulo, já existe desde a Fase 2) vira o ícone de
play. Precisa de um novo `pause` (duas barras verticais):

```js
pause: "M6 4h3v12H6V4zm5 0h3v12h-3V4z",
```

## `MediaItemRow.vue` — botão play/pause opcional

Nova prop `previewUrl` (String, default `null`). Quando presente,
mostra um botão de play/pause entre as infos e o link externo — igual
o padrão já usado pro `url`/link externo, incluindo `@click.stop`
(essencial: `MediaItemRow` já é envolvido num `<button
class="media-item-clickable">` clicável em Seguindo/Minhas Playlists
desde a Fase 2 — sem o `.stop`, clicar em play também dispararia a
navegação de aba).

```vue
<script setup>
import Icon from "./Icon.vue";
import { usePreviewPlayer } from "../composables/usePreviewPlayer.js";

const props = defineProps({
  image: { type: String, default: null },
  title: { type: String, required: true },
  subtitle: { type: String, default: "" },
  url: { type: String, default: null },
  previewUrl: { type: String, default: null },
});

const { playingUrl, toggle } = usePreviewPlayer();
</script>

<template>
  <div class="media-item-row">
    <img v-if="image" :src="image" :alt="title" class="media-item-image">
    <div v-else class="media-item-image"></div>
    <div class="media-item-info">
      <div class="media-item-title">{{ title }}</div>
      <div v-if="subtitle" class="media-item-subtitle">{{ subtitle }}</div>
    </div>
    <button
      v-if="previewUrl"
      type="button"
      class="media-item-link"
      :aria-label="playingUrl === previewUrl ? 'Pausar prévia' : 'Tocar prévia (30s)'"
      @click.stop="toggle(previewUrl)"
    >
      <Icon :name="playingUrl === previewUrl ? 'pause' : 'player'" :size="16" />
    </button>
    <a v-if="url" :href="url" target="_blank" rel="noopener" class="media-item-link" aria-label="Abrir no Spotify" @click.stop>
      <Icon name="external-link" :size="16" />
    </a>
  </div>
</template>
```

Reaproveita a classe `.media-item-link` existente (já estilizada como
ícone clicável) pro novo botão — sem CSS novo necessário aqui.

## `TrackPreview.vue` — mesmo botão no card grande

Usado pela aba Track & Audio e pelo "tocando agora" do Player. Lê
`track.preview_url` direto (já recebe o objeto track cru como prop).
Adiciona o botão ao lado do link "Abrir no Spotify" existente,
reaproveitando a classe `.preview-spotify-link`:

```vue
<script setup>
import { computed } from "vue";
import { trackSummary } from "../../utils/spotifyShapes.js";
import { usePreviewPlayer } from "../../composables/usePreviewPlayer.js";
import Icon from "../Icon.vue";

const props = defineProps({
  track: { type: Object, default: null },
  audioFeatures: { type: Object, default: null },
});

const summary = computed(() => trackSummary(props.track));
const { playingUrl, toggle } = usePreviewPlayer();
// ...resto do script inalterado (hasFeatures, features, formatDuration)
</script>
```

No template, logo após o `<a class="preview-spotify-link">` existente:

```vue
<button
  v-if="track.preview_url"
  type="button"
  class="preview-spotify-link"
  @click="toggle(track.preview_url)"
>
  <Icon :name="playingUrl === track.preview_url ? 'pause' : 'player'" :size="14" />
  {{ playingUrl === track.preview_url ? "Pausar prévia" : "Tocar prévia (30s)" }}
</button>
```

## `spotifyShapes.js` — `trackSummary()` ganha `previewUrl`

```js
export function trackSummary(track) {
  if (!track || !track.name) return null;
  return {
    image: track.album?.images?.[0]?.url ?? null,
    title: track.name,
    subtitle: asArray(track.artists).map((a) => a.name).join(", "),
    url: spotifyUrl(track),
    previewUrl: track.preview_url ?? null,
  };
}
```

`artistSummary`/`albumSummary`/`playlistSummary` não mudam (não têm
preview de áudio).

## Tabs — passar `previewUrl` pro `MediaItemRow`

Toda chamada existente de `<MediaItemRow :image="item.image"
:title="item.title" :subtitle="item.subtitle" :url="item.url" />`
ganha `:preview-url="item.previewUrl"` — mudança mecânica de uma
linha, sem lógica nova. Onde `item` vier de `artistSummary`/
`albumSummary` (que não têm `previewUrl`), o valor é `undefined` e o
botão simplesmente não aparece — mesmo efeito de "esconder quando
ausente" já decidido, sem precisar de `if` condicional por tab.

10 pontos de uso em 7 arquivos:
- `SearchTab.vue` (1 — resultados de busca, track/artist/album misto)
- `RecommendationsTab.vue` (1)
- `ArtistTab.vue` (2 — top tracks e related artists; related artists
  não tem preview, botão nunca aparece ali)
- `AlbumTab.vue` (1)
- `PlaylistTab.vue` (1)
- `MeusDadosTab.vue` (3 — top tracks/artists, curtidas, recentes)
- `PlayerTab.vue` (1 — fila)

## Testes

Sem suíte de testes JS (convenção já estabelecida) — verificação via
`npm run build` + revisão estrutural. Sem mudança de backend
(`preview_url` já passa direto em todo endpoint de track existente,
sem endpoint novo).

## Fora de escopo

- Barra de progresso/volume/seek do preview — só play/pause, 30s é
  curto o suficiente pra não precisar.
- Persistir preview tocando entre troca de aba — a troca de
  `activeTab` não desmonta `MediaItemRow`/`TrackPreview` (KeepAlive),
  mas trocar de aba não precisa parar o áudio; deixa tocando até o fim
  ou até o usuário pausar/tocar outra — comportamento natural do
  `<audio>` compartilhado, sem lógica extra necessária.
- Indicar visualmente quando `preview_url` é `null` (decidido:
  esconder o botão, não mostrar desabilitado).
