# Spotify API Explorer — Redesign Visual e de UX

**Data:** 2026-09-02
**Branch:** `feature/spotify-api-explorer` (continuação do PR #4)

## Objetivo

O frontend Vue recém-migrado é funcionalmente equivalente ao vanilla-JS
anterior, mas visualmente idêntico a ele: formulários genéricos, abas
simples, resultado só como JSON cru. O usuário quer uma ferramenta que
pareça de verdade, não "mais do mesmo" — redesign visual completo
(identidade Spotify) + melhorias reais de usabilidade (preview dos
dados, histórico, cópia, estados de carregamento/vazio), sem introduzir
dependências npm novas e sem tocar no backend Flask (esse redesign é
100% frontend).

Paridade funcional NÃO é mais o objetivo aqui — ao contrário da migração
Vue anterior, esta tarefa é explicitamente sobre melhorar a experiência,
não replicá-la 1:1. Os 18 endpoints `/api/*` continuam exatamente como
estão; tudo muda é como o frontend os consome e apresenta.

## Direção visual

Identidade visual do próprio Spotify, dark-only (sem toggle claro/escuro
— o app do Spotify também não tem, e reduz o trabalho de manter duas
paletas):

```css
--bg-base: #121212;        /* fundo da área principal */
--bg-sidebar: #000000;     /* sidebar */
--bg-elevated: #181818;    /* cards, painéis */
--bg-elevated-hover: #282828;
--accent: #1db954;         /* verde Spotify */
--accent-hover: #1ed760;
--text-primary: #ffffff;
--text-secondary: #b3b3b3;
--text-muted: #6a6a6a;
--border: rgba(255, 255, 255, 0.1);
--error: #f15e6c;
```

Tipografia: `system-ui` (sem webfont externo — zero requisição de rede
nova, zero dependência), pesos 700/800 em títulos e nomes de
faixa/artista pra dar o peso visual característico do Spotify.

Ícones: SVG inline via um componente `Icon.vue` com um pequeno registro
de paths (`{ search: "...", track: "...", ... }`) — sem lib de ícones
npm.

## Layout: sidebar

Sidebar fixa à esquerda (~240px, fundo `--bg-sidebar`):
- Topo: título "Spotify API Explorer" + indicação visual de que é uma
  dev tool (não o produto Spotify)
- Nav: um item por aba, ícone + label, estado ativo com barra verde à
  esquerda + fundo `--bg-elevated` (like Spotify's own sidebar active
  state)
- Rodapé: status do usuário (nome logado + link "Desconectar", ou botão
  "Conectar Spotify" quando deslogado) — substitui o antigo
  `#user-status` do header

Área principal: banner de credenciais faltando / erro de login (se
houver, mesma lógica de hoje) no topo, depois o conteúdo da aba ativa
(formulário + resultado).

**Responsivo:** abaixo de 768px a sidebar vira uma barra horizontal no
topo (nav com scroll horizontal se necessário) — mantém a ferramenta
utilizável numa janela estreita sem construir um menu hambúrguer/drawer
(fora de escopo, YAGNI pra uma dev tool de uso majoritariamente
desktop).

## Arquitetura de componentes

```
spotify_explorer/frontend/src/
  style.css                     # reescrito: tokens Spotify + base
  App.vue                       # sidebar em vez de nav de abas no topo
  components/
    AppSidebar.vue                # novo
    Icon.vue                      # novo — registro de ícones SVG inline
    ResultPanel.vue               # novo — status pill + copiar + skeleton +
                                    # empty state + slot de preview + JsonViewer,
                                    # compartilhado por todas as 5 abas
    SkeletonBlock.vue              # novo — placeholder animado
    EmptyState.vue                  # novo — dica contextual pré-primeira-busca
    MediaItemRow.vue                 # novo — linha reutilizável (capa + título +
                                       # subtítulo) pra listas de track/artist/album
    JsonViewer.vue                    # alterado — cores por tipo primitivo
    previews/
      TrackPreview.vue                 # novo — card "hero" da aba Track & Audio
      ArtistPreview.vue                 # novo — card "hero" da aba Artist
  composables/
    useApi.js                          # alterado — adiciona `loading` reativo
    useAuthStatus.js                    # inalterado
    useHistory.js                        # novo — histórico recente por aba
                                           # (localStorage), 10 itens, add()/items
  utils/
    spotifyShapes.js                     # novo — trackSummary(track)/
                                           # artistSummary(artist)/albumSummary(album)
                                           # → {image, title, subtitle} | null,
                                           # defensivo contra campos ausentes
  tabs/
    SearchTab.vue                         # reescrita
    TrackTab.vue                           # reescrita
    ArtistTab.vue                           # reescrita
    RecommendationsTab.vue                   # reescrita
    MeusDadosTab.vue                          # reescrita
```

Nenhuma dependência nova no `package.json` — tudo com Vue puro + CSS.

### `ResultPanel.vue`

O componente central da mudança de UX. Toda aba hoje repete a mesma
estrutura manual (`<p class="status">...</p><div class="result">...`) —
`ResultPanel` centraliza isso e adiciona o que falta:

- Props: `status` (o objeto `{text, className}` de `useApi`), `loading`
  (boolean), `data` (o JSON da resposta), `emptyHint` (string, mostrada
  no `EmptyState` antes da primeira busca)
- Slot `#preview` — cada aba injeta seu preview específico (lista de
  `MediaItemRow`, `TrackPreview`, `ArtistPreview`) quando `data !==
  null`; se a aba não passar o slot, só o JSON aparece (fallback seguro)
- Comportamento: `loading` → `SkeletonBlock`; senão `data === null` →
  `EmptyState` com `emptyHint`; senão → slot de preview (se houver) +
  status pill + botão "Copiar JSON" + `JsonViewer` colapsável

### `useApi.js` — adição de `loading`

```javascript
export function useApi() {
  const status = reactive({ text: "", className: "status" });
  const loading = ref(false);

  async function call(url, options = {}) {
    loading.value = true;
    status.text = "Carregando...";
    status.className = "status";

    const result = await fetchJSON(url, options);
    loading.value = false;
    // ...resto igual (atualiza status.text/className, retorna result)
  }

  return { status, loading, call };
}
```

Mudança aditiva — `status`/`call` continuam com a mesma assinatura,
`fetchJSON` não muda. Nenhum call site existente quebra.

### `useHistory.js`

```javascript
export function useHistory(key, limit = 10) {
  const storageKey = `spotify-explorer:history:${key}`;
  const items = ref(JSON.parse(localStorage.getItem(storageKey) || "[]"));

  function add(value) {
    if (!value) return;
    items.value = [value, ...items.value.filter((v) => v !== value)].slice(0, limit);
    localStorage.setItem(storageKey, JSON.stringify(items.value));
  }

  return { items, add };
}
```

Uma chave por aba (`search`, `track`, `artist`, `recommendations`) —
cada tab chama `add(valor)` no submit e renderiza `items` como chips
clicáveis que preenchem o campo de novo. `localStorage` falha
silenciosamente se bloqueado (modo privado, etc.) — envolver leitura e
escrita em `try/catch`, cair pra lista vazia sem quebrar a página (mesmo
cuidado defensivo já aplicado noutros pontos do app).

### `spotifyShapes.js`

Três funções puras, cada uma defensiva contra campos ausentes/nulos
(a API real pode devolver objetos parciais, erros, ou o group ainda não
ter Extended Quota pra alguns campos):

```javascript
export function trackSummary(track) {
  if (!track || !track.name) return null;
  return {
    image: track.album?.images?.[0]?.url ?? null,
    title: track.name,
    subtitle: (track.artists ?? []).map((a) => a.name).join(", "),
  };
}

export function artistSummary(artist) {
  if (!artist || !artist.name) return null;
  return {
    image: artist.images?.[0]?.url ?? null,
    title: artist.name,
    subtitle: artist.followers?.total != null
      ? `${artist.followers.total.toLocaleString("pt-BR")} seguidores`
      : (artist.genres ?? []).join(", "),
  };
}

export function albumSummary(album) {
  if (!album || !album.name) return null;
  return {
    image: album.images?.[0]?.url ?? null,
    title: album.name,
    subtitle: (album.artists ?? []).map((a) => a.name).join(", "),
  };
}
```

Retornam `null` quando o objeto não tem o formato esperado (ex: um
corpo de erro `{"error": {...}}` do Spotify) — quem chama sempre
verifica antes de renderizar um `MediaItemRow`, caindo de volta pro
JSON cru se não reconhecer o formato. Isso é o que torna o preview
seguro mesmo diante de 403/404/erros de rede: nunca quebra, só deixa de
mostrar o card bonito e mostra o JSON como sempre mostrou.

### `MediaItemRow.vue`

```
Props: image (string|null), title (string), subtitle (string)
```

Capa 48×48 (placeholder com ícone de nota musical se `image` for
`null`), título em negrito, subtítulo em `--text-secondary`, layout
flex horizontal. Usado em listas (Search, Recommendations, Meus dados,
top tracks do Artist).

## Mapeamento de preview por aba

- **Search** — resultado de `/search` tem `tracks.items[]` /
  `artists.items[]` / `albums.items[]` dependendo do `type` escolhido;
  a aba mapeia a lista correspondente por `trackSummary`/
  `artistSummary`/`albumSummary` e renderiza como lista de
  `MediaItemRow`
- **Track & Audio** — `TrackPreview.vue`: capa grande (150×150),
  nome, artista(s), duração formatada (`ms` → `m:ss`) vindos de
  `trackSummary`/campos brutos de `track`; se `audio_features` não for
  um 403 (tem `danceability`/`energy`/`valence` numéricos), mostra 3
  barras horizontais simples (`width: {valor*100}%`) — sem gráfico de
  biblioteca, só `<div>` com largura calculada
- **Artist** — `ArtistPreview.vue`: foto, nome, gêneros (chips),
  seguidores, vindos de `artistSummary`; abaixo, lista de
  `MediaItemRow` pros top tracks (`trackSummary` por item) e uma fileira
  de avatares pros related artists (foto + nome, sem subtítulo)
- **Recommendations** — lista de `MediaItemRow` das `tracks[]`
  retornadas (`trackSummary` por item)
- **Meus dados** — os 3 blocos (top tracks/artists, curtidas, recentes)
  usam listas de `MediaItemRow`; "recently played" tem formato
  `{items: [{track: {...}, played_at: "..."}]}` — a aba extrai
  `item.track` antes de passar pro `trackSummary`

Em todos os casos, se a resposta for um erro (403, 404, corpo
inesperado) ou o formato não bater com o que a função `*Summary`
espera, `MediaItemRow`/preview simplesmente não renderiza (a função
retorna `null`) e só o JSON cru aparece — que é exatamente o
comportamento de hoje, preservado como fallback.

## Empty states e dicas por aba

Cada aba passa um `emptyHint` pro `ResultPanel`:
- Search: "Digite um termo e escolha o tipo pra buscar no catálogo"
- Track & Audio: "Cole um Track ID, ex: 11dFghVXANMlKmJXsNCbNl"
- Artist: "Cole um Artist ID, ex: 0TnOYISbd1XYRBk9myaseg"
- Recommendations: "Preencha ao menos um seed (genre/track/artist)"
- Meus dados: sem `emptyHint` genérico — cada bloco (top/curtidas/
  recentes) usa o próprio botão como call-to-action

## Cópia e histórico

- `ResultPanel` tem um botão "Copiar JSON" que faz
  `navigator.clipboard.writeText(JSON.stringify(data, null, 2))` e
  mostra "Copiado!" por ~2s antes de voltar ao texto original. Sem
  cópia por nó individual — YAGNI, o botão único cobre o caso de uso
  real (levar a resposta pra outro lugar pra inspecionar/documentar).
- Histórico: chips horizontais acima do formulário de cada aba (exceto
  Meus dados, que não tem campo de texto livre), mostrando os últimos
  valores buscados; clicar um chip preenche o campo correspondente
  (não busca automaticamente — o usuário ainda clica "Buscar", mantendo
  controle explícito sobre quando uma chamada de rede acontece).

## Fora de escopo

- Qualquer mudança no backend Flask (`app.py`, `spotify_client.py`,
  `user_auth.py`) — puramente frontend
- Toggle claro/escuro
- Cópia por nó individual do JSON
- Menu hambúrguer/drawer mobile — só o colapso simples de sidebar→barra
  horizontal
- Testes JS automatizados (Vitest) — mesma convenção já estabelecida:
  verificação via `npm run build` + revisão manual/estrutural
- Gráficos de audio-features além das 3 barras simples (sem lib de
  chart)
