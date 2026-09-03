# Spotify API Explorer — Player, Seguindo, Minhas Playlists (Fase 2)

**Data:** 2026-09-02
**Branch:** `feature/spotify-explorer-phase-2` (continuação, PR próprio — a PR da Fase 1 já foi mergeada)

## Objetivo

Cobrir os 3 pedaços de API explicitamente deixados de fora da Fase 1
por exigirem escopos OAuth novos e re-login: reprodução atual
(`/me/player`), artistas seguidos (`/me/following`) e "minhas
playlists" (`/me/playlists`, que precisa de `playlist-read-private`
pra listar as privadas do usuário).

**Fora de escopo:** controles de reprodução (play/pause/skip/volume —
mudam a reprodução real do usuário; essa ferramenta só lê estado,
nunca escreve) e polling automático no Player (mesmo padrão
click-to-fetch das outras abas, sem timers).

## Escopos OAuth & re-login

`user_auth.py`:

```python
SCOPES = "user-top-read user-library-read user-read-recently-played user-read-playback-state user-read-currently-playing user-follow-read playlist-read-private"
```

Quem já tiver uma sessão logada (token/refresh token salvo de antes)
precisa deslogar e logar de novo — o token antigo não tem os escopos
novos, e a Spotify só pede consentimento deles numa nova autorização.
Documentar isso no `README.md` do explorer (mesma seção de smoke
test), sem tentar detectar/forçar isso automaticamente no código: é
comportamento esperado do OAuth, não um bug a corrigir.

## Backend — 3 rotas novas

Mesmo padrão de `_user_data_route` (Authorization Code Flow, exige
login, `_user_data_route` já centraliza o `401` de "não logado"):

```python
@app.route("/api/me/player")
def player():
    return _user_data_route("/me/player")

@app.route("/api/me/player/queue")
def player_queue():
    return _user_data_route("/me/player/queue")

@app.route("/api/me/following")
def following():
    return _user_data_route(
        "/me/following",
        params={
            "type": "artist",
            "limit": request.args.get("limit", "20"),
        },
    )

@app.route("/api/me/playlists")
def my_playlists():
    return _user_data_route(
        "/me/playlists",
        params={
            "limit": request.args.get("limit", "20"),
            "offset": request.args.get("offset", "0"),
        },
    )
```

### Fix: `call_api` não trata 204 No Content

`GET /me/player` e `GET /me/player/queue`(*) devolvem **204** (corpo
vazio) quando não há reprodução ativa. Hoje `spotify_client.call_api`
chama `response.json()` incondicionalmente, e um corpo vazio faz isso
lançar `ValueError`, caindo no branch de erro
(`{"error": "invalid_response", ...}`) — um 204 (sucesso, "nada
tocando") vira um falso erro. Fix pontual em `call_api`:

```python
def call_api(path, token, params=None):
    try:
        response = requests.get(...)
    except requests.exceptions.RequestException as exc:
        return {"error": "connection_error", "error_description": str(exc)}, 502

    if response.status_code == 204:
        return {}, 204

    try:
        body = response.json()
    ...
```

(*) `/me/player/queue` na prática sempre devolve `{currently_playing,
queue}` mesmo sem reprodução ativa (queue vazia), mas o fix cobre os
dois endpoints por igual — mais simples que tratar caso a caso, e não
quebra nenhuma rota existente (nenhuma delas retorna 204 hoje).

Testes: 4 rotas novas em `test_app_auth.py` (200, 401 sem login),
mais 1 teste do fix de 204 em `test_spotify_client.py`.

## Navegação entre abas

Hoje cada aba (`SearchTab`, `PlaylistTab`, etc.) é independente — sem
estado compartilhado entre elas. Pra "clicar num item de Minhas
Playlists abre a aba Playlist já com o ID preenchido" (e o mesmo pra
Seguindo → Artist), preciso de um jeito de uma aba pedir "troca pra
aba X com este ID" pro `App.vue`, que é quem controla `activeTab`.

Composable novo `useTabNavigation.js`, mesmo padrão de estado
module-scoped já usado em `useAuthStatus.js` (sem prop-drilling, sem
Vuex/Pinia — não precisa, é um valor só):

```js
// useTabNavigation.js
import { ref } from "vue";

const pending = ref(null); // { tab: "playlist", id: "37i9..." } | null

export function useTabNavigation() {
  function goTo(tab, id) {
    pending.value = { tab, id };
  }
  function consume(forTab) {
    if (pending.value?.tab !== forTab) return null;
    const id = pending.value.id;
    pending.value = null;
    return id;
  }
  return { pending, goTo, consume };
}
```

- `App.vue`: `watch(pending, (nav) => { if (nav) activeTab.value = nav.tab; })`
- `PlaylistTab.vue` / `ArtistTab.vue`: no `onMounted`, chamam
  `consume("playlist")` / `consume("artist")` — se vier um ID,
  preenchem o campo local e disparam a busca automaticamente (mesma
  função que o botão "Buscar" já chama). Como as abas ficam vivas via
  `KeepAlive`, `onMounted` só dispara na primeira vez que a aba é
  criada — então o consumo real precisa rodar num `watch(pending, ...)`
  dentro de cada aba-alvo também (ativado só quando `pending.tab`
  bate com a própria aba), não só no mount.

## Frontend — 3 abas novas

Mesmo padrão visual das abas atuais: `ResultPanel` (skeleton/empty
state/erro/dados), botão de ação, ícone novo em `Icon.vue` (inline
SVG).

### Player

Botão "Atualizar" chama `/api/me/player` e `/api/me/player/queue` em
paralelo. Corpo vazio (204) é tratado como empty-state normal
("Nada tocando no momento"), não como erro — `ResultPanel` já
distingue "sem dado, sem erro" de "erro" (herda a distinção que já
existe hoje pra "nunca buscou").

Conteúdo quando há reprodução ativa:
- `TrackPreview` reaproveitado pro item tocando (`item` de
  `/me/player`, mesmo formato de track que as outras abas já usam)
- Barra de progresso: `progress_ms` / `item.duration_ms`
- Dispositivo ativo: nome, tipo, volume (`device.name`,
  `device.type`, `device.volume_percent`)
- Shuffle/repeat (`shuffle_state`, `repeat_state`) como texto simples
- Fila (`queue[]` de `/me/player/queue`) como lista `MediaItemRow`

### Seguindo

Botão "Buscar" + campo `limit`. `GET /me/following` devolve
`{artists: {items: [...]}}` — lista via `ArtistPreview`/
`MediaItemRow` (`artistSummary`, já existe). Clique num item →
`goTo("artist", artist.id)`.

### Minhas Playlists

Botão "Buscar" + campo `limit`. `GET /me/playlists` devolve
`{items: [...]}` — cada item já tem o formato de `playlistSummary`
(existe desde a Fase 1). Lista via `MediaItemRow`, com indicador
extra de pública/privada (`item.public`) e "por {owner.display_name}"
como subtitle (já é o que `playlistSummary` gera). Clique num item →
`goTo("playlist", playlist.id)`.

## Sidebar

3 itens novos, com ícones distintos dos já usados (nota musical/onda
sonora pra Player, coração+pessoa ou similar pra Seguindo, pasta pra
Minhas Playlists) — inline SVG no `Icon.vue` existente.

## Fora de escopo

- Controles de reprodução (play/pause/skip/seek/volume) — exigiria
  `user-modify-playback-state` e escreveria na conta real do usuário;
  a ferramenta é só-leitura em todas as abas até aqui, mantém a
  consistência
- Polling automático na aba Player — mesmo padrão click-to-fetch de
  todas as outras abas
- Testes JS automatizados — mesma convenção já estabelecida
  (`npm run build` + revisão estrutural, wiring temporário em
  `App.vue` pra confirmar que cada `.vue` novo compila antes de
  reverter)
