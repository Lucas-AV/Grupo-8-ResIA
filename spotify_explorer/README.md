# Spotify API Explorer

Dev tool interna do Grupo 8 pra explorar a Web API do Spotify: quais
endpoints existem, quais dados retornam, e quais restrições reais existem
hoje. Não faz parte do produto final — ver
`docs/superpowers/specs/2026-09-01-spotify-api-explorer-design.md` pro
design completo.

## Setup

1. Crie um app em https://developer.spotify.com/dashboard
2. Em "Redirect URIs" do app, adicione `http://127.0.0.1:5000/callback`
   (necessário mesmo se você só for usar as abas de catálogo, sem login)
3. Copie `.env.example` para `.env` dentro de `spotify_explorer/` e
   preencha `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` com os do seu
   app. Gere um valor aleatório para `FLASK_SECRET_KEY` (ex:
   `python -c "import secrets; print(secrets.token_hex(32))"`)
4. Instale as dependências do backend:
   ```
   pip install -r requirements.txt -r spotify_explorer/requirements.txt
   ```
5. Instale as dependências do frontend e gere o build:
   ```
   cd spotify_explorer/frontend
   npm install
   npm run build
   cd ..
   ```
6. Rode o backend (que já serve o frontend buildado):
   ```
   python app.py
   ```
7. Abra `http://127.0.0.1:5000`

> **Se você já tinha uma sessão logada de antes da Fase 2:** os escopos
> do OAuth mudaram (`user-read-playback-state`,
> `user-read-currently-playing`, `user-follow-read`,
> `playlist-read-private` foram adicionados). Deslogue e logue de novo
> — a Spotify só pede consentimento dos escopos novos numa nova
> autorização; um token antigo não os tem.

## Rodando os testes

```
cd spotify_explorer
pytest
```

Todos os testes usam `requests` mockado — nenhum bate na API real, então
não precisam de credenciais.

## Desenvolvendo o frontend (hot-reload)

Pra mexer nos componentes Vue com hot-reload, em vez do passo 5-6 acima,
rode dois processos em paralelo:

```
# terminal 1 — backend
python app.py

# terminal 2 — frontend com hot-reload
cd spotify_explorer/frontend
npm run dev
```

Abra `http://127.0.0.1:5173` (não a `:5000`) — o Vite serve o frontend
com hot-reload e proxeia `/api`, `/login`, `/logout`, `/callback` pro
Flask automaticamente. Pra isso funcionar com o login (OAuth), adicione
`FRONTEND_URL=http://127.0.0.1:5173` no `.env` — sem isso, depois do
login a Spotify te devolve pra `:5000` (o Flask), não pro Vite.

## O que cada aba faz

- **Search** — `GET /search` do catálogo (track/artist/album)
- **Track & Audio** — `GET /tracks/{id}`, `/audio-features/{id}`,
  `/audio-analysis/{id}`
- **Artist** — `GET /artists/{id}` + top-tracks + albums + related-artists
- **Album** — `GET /albums/{id}` (dados + faixas)
- **Playlist** — `GET /playlists/{id}` (dados + faixas — só playlists
  públicas, Client Credentials não vê playlist privada de terceiros)
- **New Releases** — `GET /browse/new-releases`
- **Recommendations** — `GET /recommendations` com seeds e parâmetros alvo
- **Meus dados** — requer login (Authorization Code Flow): top
  tracks/artists por `time_range`, faixas curtidas, tocadas recentemente
- **Player** — `GET /me/player` (o que tá tocando, dispositivo,
  progresso) + `GET /me/player/queue` (fila) — só leitura, sem
  controles de reprodução. Requer login.
- **Seguindo** — `GET /me/following?type=artist` (artistas seguidos).
  Clicar num artista abre os detalhes na aba Artist. Requer login.
- **Minhas Playlists** — `GET /me/playlists` (inclui privadas do
  usuário logado). Clicar numa playlist abre os detalhes na aba
  Playlist. Requer login.

## Restrições conhecidas da API (não são bugs da ferramenta)

Desde nov/2024 apps novos sem "Extended Quota Mode" recebem 403 em
`audio-features`, `audio-analysis`, `recommendations` e
`related-artists`. A ferramenta mostra esse 403 como veio — é justamente
o dado que o grupo quer descobrir.

`/me/player/recently-played` devolve no máximo as últimas 50 faixas
tocadas — não é um histórico de 6 meses. Pra "mais ouvidas nos últimos ~6
meses", use a aba Meus dados com `time_range=medium_term`, que é um
ranking por frequência calculado pela Spotify, não uma lista cronológica.

`/me/player` e `/me/player/queue` devolvem 204 (sem corpo) quando não
há reprodução ativa — a ferramenta mostra isso como "Nada tocando no
momento", não como erro.

Desde fev/2026 a Spotify removeu `GET /browse/new-releases` pra apps em
Development Mode (sem alternativa/endpoint substituto) — a aba New
Releases vai mostrar 403 pra qualquer app que não esteja em Extended
Quota Mode. Mesmo caso dos 403 acima: é a API real, não bug da
ferramenta.

## Checklist de smoke test manual

- [ ] App sobe sem `.env` preenchido e mostra o aviso de credenciais faltando
- [ ] Search retorna resultados reais pra uma query conhecida
- [ ] Track & Audio retorna a track; audio-features/audio-analysis
      retornam dado ou 403 (dependendo do nível de acesso do seu app)
- [ ] Artist retorna os 4 blocos de dados
- [ ] Recommendations retorna tracks (ou 403, mesma observação acima)
- [ ] Login funciona e volta pra `/` autenticado
- [ ] Top tracks/artists funciona nas 3 janelas de tempo
- [ ] Faixas curtidas e tocadas recentemente retornam dado real
- [ ] Logout funciona e volta ao estado deslogado
- [ ] Player mostra "Nada tocando" quando não há reprodução ativa, e
      o estado real (faixa/dispositivo/fila) quando há
- [ ] Seguindo lista os artistas seguidos; clicar num item abre a aba
      Artist com os detalhes
- [ ] Minhas Playlists lista as playlists (inclusive privadas);
      clicar num item abre a aba Playlist com os detalhes
