# Spotify API Explorer — Design

**Data:** 2026-09-01
**Branch:** `feature/spotify-api-explorer`

## Objetivo

Ferramenta interna (dev tool), não parte do produto final. Serve para o
grupo explorar a Web API do Spotify na prática: quais endpoints existem,
quais dados cada um retorna, quais parâmetros aceitam, e quais restrições
reais existem hoje — para embasar decisões sobre quais dados usar no
dataset/agente de recomendação.

Não é um protótipo de feature de produto: sem login de usuário, sem
persistência de dados coletados, sem integração com o pipeline de análise
existente (`analise_mercado_streaming/`, `scripts/`, `site/`).

## Restrição conhecida da API

Desde nov/2024 a Spotify restringiu, para apps novos sem "Extended Quota
Mode" aprovado, o acesso a: `audio-features`, `audio-analysis`,
`recommendations`, `related-artists` e preview de 30s. Apps criados depois
dessa data recebem 403 nesses endpoints por padrão.

A ferramenta **não tenta contornar ou mascarar isso** — o objetivo é
justamente descobrir o que a API permite hoje. Erros da Spotify (403, 404,
429 com `Retry-After`, etc.) são repassados ao frontend como vieram, com
status code visível.

## Escopo de auth

Client Credentials Flow apenas (sem login/redirect de usuário) — cobre
todos os endpoints públicos do catálogo (search, tracks, artists, albums,
audio-features/analysis, recommendations). Não cobre dados pessoais do
usuário (top tracks, playlists, recently played) — fora de escopo desta
ferramenta.

Credenciais (`SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET`) via `.env`
local, gitignored. Cada integrante do grupo cria seu próprio app no
[Spotify Developer Dashboard](https://developer.spotify.com/dashboard).

## Arquitetura

Diretório isolado na raiz do repo, sem dependência do resto do projeto
(que hoje é análise de dados em Python/Julia + site estático Jinja2, sem
nenhum servidor):

```
spotify_explorer/
  app.py               # Flask app + registro das rotas /api/*
  spotify_client.py    # Client Credentials: obtém/cacheia token, faz requests à Web API
  requirements.txt     # flask, requests, python-dotenv (separado do requirements.txt raiz)
  .env.example          # SPOTIFY_CLIENT_ID=, SPOTIFY_CLIENT_SECRET=
  templates/
    index.html          # página única, abas por categoria de endpoint
  static/
    app.js              # fetch() para as rotas /api/*, render de JSON colapsável
    style.css
  README.md             # como criar app no dashboard e rodar local
  test_spotify_client.py # teste do cache/renovação de token (mockado)
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

### Frontend (`templates/index.html` + `static/app.js`)

Página única com 4 abas:

1. **Search** — campo de busca + tipo + limit
2. **Track & Audio** — ID da track → busca track, audio-features e
   audio-analysis de uma vez
3. **Artist** — ID do artista → dados do artista, top tracks, albums,
   related artists
4. **Recommendations** — seeds + target params

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

## Testes

Um teste unitário (`pytest`) para `spotify_client.py`: cache de token,
renovação quando expira, usando `requests` mockado — sem bater na API
real (sem credenciais em CI). Consistente com o uso de `pytest` já
existente no `requirements.txt` raiz.

## Fora de escopo

- Login de usuário / Authorization Code Flow
- Persistência dos dados explorados (banco, arquivos)
- Integração com o pipeline de análise (`analise_mercado_streaming/`,
  `scripts/`, `site/`)
- Deploy — é uma ferramenta local de desenvolvimento
