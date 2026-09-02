# Spotify API Explorer — Expansão de Catálogo (Fase 1)

**Data:** 2026-09-02
**Branch:** `feature/spotify-api-explorer` (continuação do PR #4)

## Objetivo

Duas coisas, no mesmo lote de trabalho porque se apoiam na mesma
infraestrutura (`MediaItemRow`, `spotifyShapes.js`, o padrão
tab-com-`ResultPanel` já estabelecido):

1. **Polimento das 5 abas atuais** — expor dados que a Spotify já
   devolve mas hoje só aparecem no JSON cru: link "Abrir no Spotify" em
   qualquer item de lista/preview, popularidade e selo "Explicit" nos
   cards de Track/Artist.
2. **3 abas novas de catálogo** — Album, Playlist (pública) e New
   Releases — cobrindo mais superfície da Web API do Spotify, todas
   sem exigir login (Client Credentials Flow, igual às 5 abas atuais
   de catálogo).

**Fora de escopo desta fase** (vai pra uma spec separada, Fase 2, por
exigir escopos OAuth novos e re-login): reprodução atual (`/me/player`),
artistas seguidos (`/me/following`), e "minhas playlists"
(`/me/playlists`, que precisa do escopo `playlist-read-private` pra
listar playlists privadas do usuário).

## Backend — 3 rotas novas

Mesmo padrão das rotas de catálogo existentes: `spotify_client.api_get`
(Client Credentials, sem login), retorna o JSON da Spotify como veio,
com o status HTTP real.

```python
@app.route("/api/album/<album_id>")
def album(album_id):
    body, status = spotify_client.api_get(
        f"/albums/{album_id}",
        app.config["SPOTIFY_CLIENT_ID"],
        app.config["SPOTIFY_CLIENT_SECRET"],
    )
    return jsonify(body), status

@app.route("/api/playlist/<playlist_id>")
def playlist(playlist_id):
    body, status = spotify_client.api_get(
        f"/playlists/{playlist_id}",
        app.config["SPOTIFY_CLIENT_ID"],
        app.config["SPOTIFY_CLIENT_SECRET"],
    )
    return jsonify(body), status

@app.route("/api/new-releases")
def new_releases():
    body, status = spotify_client.api_get(
        "/browse/new-releases",
        app.config["SPOTIFY_CLIENT_ID"],
        app.config["SPOTIFY_CLIENT_SECRET"],
        params={"limit": request.args.get("limit", "20")},
    )
    return jsonify(body), status
```

`GET /albums/{id}` e `GET /playlists/{id}` da Spotify já devolvem as
faixas embutidas (`tracks.items[]`, paginado a 50/100) — não precisa de
uma rota separada pra "faixas do álbum/playlist". `GET
/browse/new-releases` devolve `{albums: {items: [...]}}`.

Testado com `pytest` (mockado, mesmo padrão de todas as outras rotas)
— 3 testes novos, um por rota, seguindo exatamente o padrão dos testes
de catálogo já existentes em `test_app.py`.

## Polimento das abas existentes

### `spotifyShapes.js`

`trackSummary`/`artistSummary`/`albumSummary` passam a incluir um campo
`url` (`obj.external_urls?.spotify ?? null`) no objeto que retornam.
Nova função `playlistSummary(playlist)`, mesmo formato das outras
(`{image, title, subtitle, url}` ou `null`), com `subtitle` sendo "por
{owner.display_name}".

### `MediaItemRow.vue`

Nova prop opcional `url` (default `null`). Quando presente, mostra um
ícone pequeno de link externo à direita da linha (`target="_blank"
rel="noopener"`) — quando ausente, a linha renderiza exatamente como
hoje (mudança 100% aditiva/opt-in).

As 4 abas que já usam `MediaItemRow` (Search, Recommendations, Artist,
Meus dados) passam a repassar `:url="item.url"` em cada uso — trivial,
já que `item` ali já é o objeto retornado por uma `*Summary` function,
que agora carrega `url` automaticamente.

### `TrackPreview.vue` / `ArtistPreview.vue`

- Link "Abrir no Spotify" (usa o novo `summary.url`)
- Barra de popularidade (`track.popularity`/`artist.popularity`,
  0-100), reaproveitando visualmente o estilo das barras de
  danceability/energy/valence já existentes em `TrackPreview`
- `TrackPreview`: selo "Explicit" ao lado do título quando
  `track.explicit` for `true`

## 3 abas novas

Mesmo padrão de UI das abas de catálogo atuais: campo de ID + botão
(Album, Playlist) ou botão sem campo (New Releases), histórico de
buscas recentes (`useHistory`), `ResultPanel` com preview + JSON cru.

### Album

`AlbumPreview.vue`: capa, nome, artista(s), data de lançamento, número
de faixas, link "Abrir no Spotify". Lista de faixas do álbum via
`MediaItemRow` (as faixas retornadas dentro de um álbum não trazem capa
própria — `trackSummary` vai devolver `image: null` pra elas, o que já
é tratado com um placeholder; a capa do álbum já aparece uma vez no
topo do card).

### Playlist

`PlaylistPreview.vue`: capa, nome, "por {dono}", descrição (se houver),
número de faixas, link "Abrir no Spotify". Lista de faixas via
`MediaItemRow` — as faixas de uma playlist vêm como `tracks.items[] =
[{track: {...}, added_at, ...}]` (mesmo formato de "faixas curtidas" e
"tocadas recentemente" na aba Meus dados), então precisa desembrulhar
`item.track` antes de sumarizar, igual já é feito lá.

Só playlists **públicas** funcionam (Client Credentials não enxerga
playlist privada/colaborativa de terceiros — Spotify devolve 403/404
nesse caso, e a ferramenta mostra isso normalmente, como qualquer outro
erro).

### New Releases

Sem campo de ID — só um botão "Buscar lançamentos" (e um campo opcional
de `limit`). Lista de álbuns via `MediaItemRow` (`albumSummary` por
item de `albums.items[]`).

## Sidebar

3 itens novos na navegação lateral, com ícones distintos dos já usados
(pilha de discos pra Album, lista pra Playlist, estrela pra New
Releases) — inline SVG no `Icon.vue` existente, sem lib de ícones nova.

## Fora de escopo

- Player, Seguindo, "minhas playlists" — Fase 2 (spec separada, exige
  novos escopos OAuth e re-login)
- Testes JS automatizados — mesma convenção já estabelecida
  (`npm run build` + revisão estrutural)
- Qualquer mudança em `user_auth.py` ou no fluxo de login — essa fase é
  100% Client Credentials, não toca no OAuth de usuário
