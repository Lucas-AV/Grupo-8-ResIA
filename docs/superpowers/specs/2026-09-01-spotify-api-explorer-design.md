# Spotify API Explorer — Design

**Data:** 2026-09-01
**Branch:** `feature/spotify-api-explorer`

## Objetivo

Ferramenta interna (dev tool), não parte do produto final. Serve para o
grupo explorar a Web API do Spotify na prática: quais endpoints existem,
quais dados cada um retorna, quais parâmetros aceitam, e quais restrições
reais existem hoje — para embasar decisões sobre quais dados usar no
dataset/agente de recomendação.

Não é um protótipo de feature de produto: sem persistência de dados
coletados, sem integração com o pipeline de análise existente
(`analise_mercado_streaming/`, `scripts/`, `site/`).

Inclui uma aba de dados pessoais do usuário logado (top tracks, faixas
curtidas, tocadas recentemente) — não para construir um produto, mas para
o grupo ver na prática o que a API expõe sobre um usuário real e decidir o
que é utilizável no agente de recomendação.

## Restrição conhecida da API

Desde nov/2024 a Spotify restringiu, para apps novos sem "Extended Quota
Mode" aprovado, o acesso a: `audio-features`, `audio-analysis`,
`recommendations`, `related-artists` e preview de 30s. Apps criados depois
dessa data recebem 403 nesses endpoints por padrão.

A ferramenta **não tenta contornar ou mascarar isso** — o objetivo é
justamente descobrir o que a API permite hoje. Erros da Spotify (403, 404,
429 com `Retry-After`, etc.) são repassados ao frontend como vieram, com
status code visível.

Também não existe endpoint de "histórico cronológico" de longo prazo:

- `/me/player/recently-played` devolve só as últimas 50 faixas tocadas
  (não é 6 meses de histórico).
- "Mais ouvidas nos últimos ~6 meses" é aproximado via
  `/me/top/tracks?time_range=medium_term` — um **ranking por frequência**
  calculado pela Spotify, não uma lista cronológica de reproduções.

A ferramenta expõe os três `time_range` disponíveis (`short_term` ~4
semanas, `medium_term` ~6 meses, `long_term` vários anos) para o grupo
comparar, deixando claro que é ranking e não histórico.

## Escopo de auth

Dois fluxos, para dois tipos de dado:

- **Client Credentials Flow** (sem login) — cobre o catálogo público:
  search, tracks, artists, albums, audio-features/analysis,
  recommendations.
- **Authorization Code Flow** (login do usuário via navegador) — cobre
  dados pessoais do usuário logado: top tracks/artists, faixas curtidas
  (saved tracks), tocadas recentemente. Scopes necessários:
  `user-top-read`, `user-library-read`, `user-read-recently-played`.

Credenciais (`SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` /
`SPOTIFY_REDIRECT_URI` / `FLASK_SECRET_KEY`) via `.env` local, gitignored.
Cada integrante do grupo cria seu próprio app no [Spotify Developer
Dashboard](https://developer.spotify.com/dashboard) e cadastra
`http://127.0.0.1:5000/callback` como Redirect URI do app.

O token de usuário (access + refresh token) fica só na sessão Flask
(cookie assinado do lado do servidor) — nunca gravado em disco, some ao
fechar/reiniciar o app ou fazer logout.

## Arquitetura

Diretório isolado na raiz do repo, sem dependência do resto do projeto
(que hoje é análise de dados em Python/Julia + site estático Jinja2, sem
nenhum servidor):

```
spotify_explorer/
  app.py               # Flask app + registro das rotas /api/*, /login, /callback, /logout
  spotify_client.py    # Client Credentials: obtém/cacheia token app-only, faz requests à Web API
  user_auth.py         # Authorization Code Flow: gera URL de login, troca code por token,
                        # guarda/renova token de usuário na sessão Flask
  requirements.txt     # flask, requests, python-dotenv (separado do requirements.txt raiz)
  .env.example          # SPOTIFY_CLIENT_ID=, SPOTIFY_CLIENT_SECRET=, SPOTIFY_REDIRECT_URI=, FLASK_SECRET_KEY=
  templates/
    index.html          # página única, abas por categoria de endpoint
  static/
    app.js              # fetch() para as rotas /api/*, render de JSON colapsável
    style.css
  README.md             # como criar app no dashboard e rodar local
  test_spotify_client.py # teste do cache/renovação de token app-only (mockado)
  test_user_auth.py      # teste da troca/renovação de token de usuário (mockado)
```

### `spotify_client.py`

- Função para obter token: `POST https://accounts.spotify.com/api/token`
  com `grant_type=client_credentials` e Basic Auth (`client_id:client_secret`
  em base64).
- Cacheia o token em memória com o `expires_in` retornado; renova
  automaticamente quando expira ou está prestes a expirar.
- Helper genérico para chamar `GET https://api.spotify.com/v1/...` com o
  Bearer token, repassando status code e corpo da resposta (sucesso ou
  erro) sem transformação — a ferramenta é para ver a API "crua".

### `user_auth.py`

- `get_login_url()` — monta a URL de autorização
  (`accounts.spotify.com/authorize`) com `client_id`, `redirect_uri`,
  `scope` (`user-top-read user-library-read user-read-recently-played`) e
  um `state` aleatório (guardado na sessão, validado no callback contra
  CSRF).
- `exchange_code(code)` — troca o `code` do callback por
  `access_token`/`refresh_token` (`POST accounts.spotify.com/api/token`,
  `grant_type=authorization_code`), guarda ambos + expiração na sessão
  Flask.
- `get_valid_user_token()` — devolve o access token da sessão, renovando
  via `refresh_token` (`grant_type=refresh_token`) se expirado. Levanta
  erro claro (capturado por `app.py` → 401 JSON) se não houver sessão
  logada, para as rotas de "Meus dados" tratarem de forma uniforme.

### Rotas backend (`app.py`)

Todas retornam o JSON exatamente como a Spotify devolveu, mais o status
HTTP:

- `POST /api/search` — params: `q`, `type` (track/artist/album), `limit`
- `GET /api/track/<id>`
- `GET /api/audio-features/<id>`
- `GET /api/audio-analysis/<id>`
- `GET /api/artist/<id>`
- `GET /api/artist/<id>/top-tracks`
- `GET /api/artist/<id>/albums`
- `GET /api/artist/<id>/related-artists`
- `GET /api/recommendations` — `seed_tracks`/`seed_artists`/`seed_genres`
  (pelo menos um obrigatório) + `target_*` opcionais (danceability,
  energy, valence, tempo, etc.)

Auth de usuário:

- `GET /login` — redireciona para a tela de autorização da Spotify
- `GET /callback` — recebe o `code`, chama `exchange_code`, redireciona
  de volta pra `/` já logado
- `GET /logout` — limpa a sessão
- `GET /api/me` — perfil do usuário logado (nome, avatar), usado pro
  frontend saber se está logado e mostrar quem é
- `GET /api/me/top/tracks?time_range=short_term|medium_term|long_term&limit=`
- `GET /api/me/top/artists?time_range=...&limit=`
- `GET /api/me/tracks` — faixas curtidas/salvas (`GET /me/tracks`,
  paginado via `limit`/`offset`)
- `GET /api/me/player/recently-played?limit=` — últimas tocadas (máx. 50,
  limite da própria Spotify)

As rotas `/api/me/*` usam `get_valid_user_token()`; se não houver sessão
logada devolvem 401 com uma mensagem clara ("faça login primeiro"), que o
frontend usa pra mostrar o botão de login em vez de um erro genérico.

### Frontend (`templates/index.html` + `static/app.js`)

Página única com 5 abas:

1. **Search** — campo de busca + tipo + limit
2. **Track & Audio** — ID da track → busca track, audio-features e
   audio-analysis de uma vez
3. **Artist** — ID do artista → dados do artista, top tracks, albums,
   related artists
4. **Recommendations** — seeds + target params
5. **Meus dados** — se não logado, mostra botão "Conectar Spotify" (vai
   pra `/login`). Se logado: sub-seções pra top tracks/artists (seletor
   de `time_range`), faixas curtidas, e tocadas recentemente — cada uma
   com botão "Buscar" que chama a rota `/api/me/*` correspondente.
   Mostra o nome/avatar do usuário logado (via `/api/me`) e um botão
   "Desconectar".

Cada aba tem um form; submit dispara `fetch()` para a rota
correspondente, sem reload de página. Resultado exibido em bloco `<pre>`
com JSON formatado (indentado) e colapsável por chave de topo. Status
HTTP e, se erro, a mensagem de erro da Spotify ficam visíveis no topo do
resultado — é o dado mais importante da ferramenta.

## Erros e casos de borda

- Sem `.env` configurado → app sobe mas mostra aviso claro na página
  (não crasha).
- Token expirado no meio de uma sessão → `spotify_client.py` renova
  transparentmente antes do próximo request.
- 429 (rate limit) → repassa o header `Retry-After` junto do erro.
- IDs inválidos/inexistentes → repassa o 404 da Spotify como veio.
- Rota `/api/me/*` chamada sem sessão logada → 401 JSON com mensagem
  clara, sem quebrar a página.
- `state` do callback OAuth não bate com o da sessão → rejeita o login
  (proteção CSRF básica) e mostra erro.
- Refresh token inválido/revogado → limpa a sessão e pede novo login, em
  vez de ficar tentando renovar em loop.

## Testes

Testes unitários (`pytest`), sem bater na API real (sem credenciais em
CI), consistente com o uso de `pytest` já existente no `requirements.txt`
raiz:

- `test_spotify_client.py` — cache/renovação do token app-only
  (`requests` mockado).
- `test_user_auth.py` — geração da URL de login com `state`, troca de
  `code` por token, renovação via `refresh_token`, e o caso de sessão
  ausente (`requests` mockado).

## Fora de escopo

- Persistência dos dados explorados (banco, arquivos) — inclusive dados
  pessoais do usuário: nada é salvo, só passa pela sessão em memória
  durante o uso
- Integração com o pipeline de análise (`analise_mercado_streaming/`,
  `scripts/`, `site/`)
- Deploy — é uma ferramenta local de desenvolvimento
- Escrita na conta do usuário (curtir/descurtir, criar playlist, etc.) —
  só leitura (`user-top-read`, `user-library-read`,
  `user-read-recently-played`)
