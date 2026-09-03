# Spotify API Explorer — Adaptação às mudanças de fev/2026

**Data:** 2026-09-03
**Branch:** `fix/spotify-feb2026-api-changes` (a partir da `main`)

## Objetivo

Ao testar manualmente a Fase 2, descobrimos que a aba New Releases
retorna 403 — Spotify removeu `GET /browse/new-releases` pra apps em
Development Mode em fev/2026, sem substituto (já documentado no
README, commit anterior). Investigando o guia de migração oficial da
Spotify, achamos duas outras mudanças da mesma leva que afetam abas já
existentes da ferramenta (Fase 1, hoje em produção sem estar cobertas
por nenhum teste manual recente):

1. **`GET /artists/{id}/top-tracks` foi removido** — sem substituto.
   Usado pela aba Artist.
2. **Resposta de `GET /playlists/{id}` mudou de formato**: o campo
   `tracks` foi renomeado pra `items` (e o aninhado `tracks.items[].track`
   virou `items.items[].item`), e — mais importante — **o campo de
   faixas fica ausente inteiramente** quando quem chama não é o
   dono/colaborador da playlist. Como a aba Playlist usa Client
   Credentials Flow (sem usuário associado), isso pode significar que
   ela nunca mais recebe lista de faixas, só metadados.

Este spec cobre como adaptar as duas abas a isso.

## Artist — sem mudança de código

`app.py`'s `/api/artist/<id>/top-tracks` já é um passthrough puro
(`spotify_client.api_get`, sem lógica própria) — vai simplesmente
repassar o status real que a Spotify devolver (403 ou 404) pro
frontend. `ArtistTab.vue`'s `topTracksItems` computed já trata isso
sem quebrar:

```js
const topTracksItems = computed(() => {
  if (!result.data?.top_tracks?.tracks) return [];
  return result.data.top_tracks.tracks.map(trackSummary).filter((item) => item !== null);
});
```

Um `top_tracks` de erro (`{error: {...}}`) não tem `.tracks`, então
isso já devolve `[]` — a aba simplesmente não mostra a seção "Top
tracks", sem crash, exatamente como já acontece hoje com
audio-features/recommendations/related-artists quando dão 403. Único
trabalho aqui: documentar no README (mesmo padrão das restrições já
listadas).

## Playlist — fix real, só frontend

`app.py`'s `/api/playlist/<id>` também é passthrough puro — nenhuma
mudança de backend necessária. O fix é inteiramente em
`PlaylistTab.vue` e `PlaylistPreview.vue`, pra lidar com os dois
formatos possíveis (não sabemos de antemão qual a API realmente
devolve pra esse app/token — é exatamente o tipo de coisa que essa
ferramenta existe pra descobrir na prática) e com o caso de faixas
ausentes.

### `PlaylistTab.vue`

Troca o `tracks` computed atual (que só lê
`result.data.tracks.items[].track`) por uma versão que:
- Lê o container de faixas de `result.data.items` (nome novo) ou
  `result.data.tracks` (nome antigo), o que estiver presente.
- Dentro de cada entrada, lê a faixa de `entry.item` (novo) ou
  `entry.track` (antigo).
- Só considera "temos lista de faixas" quando esse container tem um
  array `.items` de verdade.

```js
const tracksContainer = computed(() => result.data?.items ?? result.data?.tracks ?? null);

const tracks = computed(() => {
  const items = tracksContainer.value?.items;
  if (!Array.isArray(items)) return [];
  return items
    .map((entry) => trackSummary(entry.item ?? entry.track))
    .filter((item) => item !== null);
});

const tracksUnavailable = computed(() => {
  if (!result.data?.name) return false;
  return !Array.isArray(tracksContainer.value?.items);
});
```

`tracksUnavailable` só fica `true` quando uma playlist de verdade foi
carregada (`result.data.name` existe — mesma checagem que
`playlistSummary()` já usa pra decidir se tem dado válido) mas nenhum
dos dois formatos trouxe um array de faixas. Uma playlist real com
zero faixas continua mostrando container presente com `items: []` —
`Array.isArray([])` é `true`, então `tracksUnavailable` fica `false`
e a seção "Faixas" simplesmente não aparece (mesmo comportamento de
hoje), sem a nota de indisponibilidade.

Template: adiciona um `v-else-if` mostrando a nota quando
`tracksUnavailable` for `true`:

```html
<div v-if="tracks.length">
  <h3>Faixas</h3>
  ...
</div>
<p v-else-if="tracksUnavailable" class="status status-error">
  Faixas não disponíveis — a Spotify só devolve o campo de faixas pra
  quem é dono/colaborador da playlist (restrição de fev/2026). Essa
  aba usa Client Credentials Flow, sem usuário associado, então nunca
  vai ver faixas de playlist nenhuma por aqui.
</p>
```

### `PlaylistPreview.vue`

A contagem "N faixas" hoje só lê `playlist.tracks?.total`. Passa a
cair pra `playlist.items?.total` quando o primeiro não existir — o
total é metadado e deve sobreviver mesmo quando o array de faixas em
si estiver ausente:

```html
<div v-if="(playlist.tracks?.total ?? playlist.items?.total) != null" class="preview-subtitle">
  {{ playlist.tracks?.total ?? playlist.items?.total }} faixas
</div>
```

## Testes

Nenhuma mudança de backend/Python — nenhum teste novo em `pytest`.
Sem suíte de testes JS (convenção já estabelecida no projeto) —
verificação via `npm run build` + revisão estrutural, mesmo padrão de
sempre.

## Fora de escopo

- Trocar a aba Playlist pra usar Authorization Code Flow (usuário
  logado) pra tentar recuperar faixas de playlists próprias — mudança
  arquitetural maior, não pedida agora. Se o teste manual mostrar que
  isso é necessário pra a aba ter utilidade, vira um spec separado.
- Qualquer mudança na aba New Releases (endpoint sem substituto,
  já documentado).
- Cobrir novas áreas da API (Shows/Episodes/Audiobooks/Genres) —
  ficou definido que essa exploração vem depois, como um trabalho
  separado.
