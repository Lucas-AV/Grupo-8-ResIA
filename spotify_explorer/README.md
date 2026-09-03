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

> **Se você já tinha uma sessão logada de antes:** os escopos do OAuth
> mudaram (`user-read-playback-state`, `user-read-currently-playing`,
> `user-follow-read`, `playlist-read-private`,
> `user-modify-playback-state`). Deslogue e logue de novo — a Spotify
> só pede consentimento dos escopos novos numa nova autorização; um
> token antigo não os tem.

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

## Login via QR code (kiosk/demo)

Além do login direto (`/login`, no mesmo dispositivo), dá pra abrir
`GET /login/qr` numa tela compartilhada (kiosk, TV, PC de demo) — ela
mostra um QR code que qualquer pessoa pode escanear com o próprio
celular pra autorizar com a própria conta Spotify. A tela do kiosk
fica fazendo polling sozinha e destrava automaticamente assim que
alguém completa o login pelo celular.

> **Cuidado — o código do QR é um "bearer token" temporário:** qualquer
> pessoa que tiver o código (não só quem escaneou a tela — também vale
> pra um link encaminhado, um print de tela ou uma captura de vídeo,
> dentro da janela de 5 minutos) consegue completar ou "roubar" esse
> pareamento, porque nada além do próprio código amarra a autorização a
> um dispositivo específico. Em outras palavras: não compartilhe o QR
> nem o link por baixo dele (`/login?pair=...`) com ninguém em quem você
> não confia, e numa demo/kiosk com várias pessoas por perto, quem
> escanear/consumir primeiro "ganha" aquele código. Isso é uma
> característica conhecida do desenho atual (aceitável pro escopo desta
> ferramenta — uso local, single-user, sem rede pública), não um bug.

**Pré-requisito:** o celular precisa estar na **mesma rede local** que
a máquina rodando o `spotify_explorer` — o QR codifica o endereço que
o navegador do kiosk usou pra abrir a página (`request.host_url`), e
esse endereço só é alcançável de outro dispositivo se for um IP de
rede local (ex.: `http://192.168.x.x:5000/`), não `127.0.0.1`. Não há
suporte a túnel (ngrok ou similar) embutido — pra demo fora da rede
local, seria preciso configurar isso manualmente.

O código do QR expira em 5 minutos e é de uso único — depois de
consumido (ou expirado), a tela do kiosk gera um QR novo sozinha.

## O que cada aba faz

- **Search** — `GET /search` do catálogo (track/artist/album)
- **Track & Audio** — `GET /tracks/{id}`, `/audio-features/{id}`,
  `/audio-analysis/{id}`
- **Artist** — `GET /artists/{id}` + top-tracks (removido pela Spotify
  em fev/2026, ver restrições abaixo) + albums + related-artists
- **Album** — `GET /albums/{id}` (dados + faixas)
- **Playlist** — `GET /playlists/{id}` (dados + metadados sempre;
  faixas só se a API devolver o campo — ver restrições abaixo, hoje
  isso nunca acontece via Client Credentials)
- **New Releases** — `GET /browse/new-releases`
- **Recommendations** — `GET /recommendations` com seeds e parâmetros alvo
- **Meus dados** — requer login (Authorization Code Flow): top
  tracks/artists por `time_range`, faixas curtidas, tocadas recentemente
- **Player** — `GET /me/player` (o que tá tocando, dispositivo,
  progresso) + `GET /me/player/queue` (fila), mais controles reais de
  reprodução (play/pause/next/previous/seek/volume/shuffle/repeat) via
  `PUT`/`POST /me/player/*` — a primeira parte da ferramenta que
  escreve de verdade na conta do usuário. Também gera uma playlist
  privada com faixas relacionadas à que está tocando agora
  (`GET /recommendations` + `POST /me/playlists` + `POST
  /playlists/{id}/items`). Requer login.
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

Na mesma leva de fev/2026, a Spotify também removeu
`GET /artists/{id}/top-tracks` (sem substituto) e mudou o formato de
`GET /playlists/{id}`: o campo `tracks` virou `items`, e o campo de
faixas fica ausente inteiramente quando quem chama não é
dono/colaborador da playlist. A aba Artist simplesmente não mostra a
seção "Top tracks" quando isso falha (mesmo tratamento dos outros 403
já citados). A aba Playlist usa Client Credentials Flow — sem usuário
associado — então mostra uma nota explícita de "Faixas não
disponíveis" em vez da lista, já que nunca vai ter permissão de
dono/colaborador nenhuma.

Os controles de reprodução (`/me/player/play`, `/pause`, `/next`,
`/previous`, `/seek`, `/volume`, `/shuffle`, `/repeat`) precisam de um
dispositivo Spotify ativo (app aberto em algum lugar logado na mesma
conta) — sem isso a Spotify devolve 404
(`NO_ACTIVE_DEVICE`/`NO_PREV_TRACK` etc.). Também exigem conta
Premium — contas free recebem 403 (`PREMIUM_REQUIRED`). A geração de
playlist relacionada depende de `GET /recommendations`, que já é um
403 conhecido desde nov/2024 pra apps sem Extended Quota Mode — o
botão provavelmente vai mostrar esse erro em vez de criar a playlist,
o que já é o comportamento esperado (documentado acima).

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
- [ ] Artist não quebra quando top-tracks falha (403/404) — só omite
      a seção
- [ ] Playlist mostra a nota "Faixas não disponíveis" pra qualquer
      playlist pública (Client Credentials nunca é dono/colaborador)
- [ ] Player mostra "Nada tocando" quando não há reprodução ativa, e
      o estado real (faixa/dispositivo/fila) quando há
- [ ] Seguindo lista os artistas seguidos; clicar num item abre a aba
      Artist com os detalhes
- [ ] Minhas Playlists lista as playlists (inclusive privadas);
      clicar num item abre a aba Playlist com os detalhes
- [ ] Play/pause/next/previous mudam o estado real no dispositivo
      ativo (ou mostram 404/403 se não houver dispositivo ativo/conta
      não for Premium)
- [ ] Seek e volume só disparam a chamada ao soltar o slider, não a
      cada movimento
- [ ] Shuffle e repeat alternam estado e refletem isso após o refetch
      automático
- [ ] Gerar playlist relacionada cria uma playlist privada de verdade
      (ou mostra o erro real do passo que falhou — recommendations,
      create_playlist ou add_items)
- [ ] `GET /login/qr` mostra um QR code de verdade e escaneável (teste
      com celular na mesma rede local)
- [ ] Escanear o QR e autorizar no celular faz a tela do kiosk
      destravar sozinha (sem recarregar manualmente)
- [ ] Um QR não escaneado por 5 minutos expira e a tela gera um novo
      sozinha
- [ ] Escanear o mesmo QR duas vezes (ou escanear um já usado) não
      funciona da segunda vez
