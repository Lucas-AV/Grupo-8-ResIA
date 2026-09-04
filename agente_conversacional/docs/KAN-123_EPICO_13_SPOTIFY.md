# Épico 13 — Spotify no produto real

Este documento é o mapa de manutenção das funcionalidades Spotify. O código de
produção fica exclusivamente em `agente_conversacional/`; o
`spotify_explorer/` continua sendo ferramenta de exploração e não deve receber
novas funcionalidades deste épico.

## Arquitetura

`frontend/spotifyHub.js` é a Central Spotify: busca, detalhes, coleções do
usuário, lançamentos, recomendações nativas, player e QR. Ela só envia o
`session_id`; o token OAuth permanece no `TokenStore`. As rotas em
`spotify_auth/routes.py` renovam o token por `get_valid_access_token` e chamam
`spotify_auth/catalog.py`, o único cliente HTTP da Web API usado por essa
central.

| Tickets | Rota do produto |
| --- | --- |
| KAN-110 a KAN-114 | `GET /spotify/search`, `/spotify/tracks/{id}`, `/spotify/artists/{id}`, `/spotify/albums/{id}`, `/spotify/playlists/{id}` |
| KAN-115, KAN-118, KAN-119 | `GET /spotify/me/playlists`, `/spotify/me/following`, `/spotify/me` |
| KAN-116, KAN-117 | `GET /spotify/new-releases`, `/spotify/recommendations` |
| KAN-120 | `GET /spotify/player`, `POST /spotify/player/{action}` e `/queue` |
| KAN-121 | `trackCard.js`: preview nativo de até 30 s, carregado sob demanda |
| KAN-122 | `POST /auth/qr`, status e aprovação de pareamento |

## QR: modelo de segurança

O QR possui segredo aleatório, expira em três minutos e só pode iniciar o OAuth.
Após a autorização no celular, os tokens ficam pendentes: a sessão que gerou o
QR deve pressionar **Confirmar pareamento** para armazená-los. Logo, uma foto ou
link encaminhado não vincula silenciosamente uma conta de terceiro ao produto.
O `PairingStore` é propositalmente efêmero; em execução multi-instância deve ser
trocado por armazenamento compartilhado com TTL e rate limit no proxy.

## Uso local e validação

1. Instale as dependências de `agente_conversacional/requirements.txt` (inclui
   `segno`, usado para gerar o SVG localmente).
2. Configure `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET` e
   `SPOTIFY_REDIRECT_URI`.
3. Execute `python scripts/check_epic13.py` e a suíte `pytest` do diretório
   `agente_conversacional`.

As capabilities da Spotify Web API podem variar por tipo de aplicação ou plano.
O frontend mostra a mensagem normalizada da API; controles Connect requerem
Premium e dispositivo ativo. Recomendações nativas são exibidas com fonte
explícita, para não se confundirem com o motor ResIA baseado no dataset.
