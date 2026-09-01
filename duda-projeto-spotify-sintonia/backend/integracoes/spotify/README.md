# Integração Spotify

Esta camada implementa OAuth pelo backend com Spotipy, coleta de perfil, top tracks e top artists, renovação de token e tratamento de rate limit.

## Escopos mínimos

- `user-top-read`: lê as faixas e artistas mais ouvidos, que são os sinais usados para formar o perfil musical.
- `user-read-private`: lê o perfil básico exibido no produto.

Não solicitamos e-mail, biblioteca, playlists nem histórico de reprodução porque não são necessários neste escopo.

## Atributos de áudio

O endpoint Spotify de áudio foi descontinuado/removido. Portanto, `catalogo.py` busca os atributos pelo `track_id` no dataset Kaggle tratado localmente; quando a faixa não existir no catálogo, a origem é registrada como indisponível. A integração nunca chama `audio_features`.

## Modos

- `SPOTIFY_MODO=demo`: três perfis fictícios (`acustico`, `energetico`, `ecletico`), adequados para testes e apresentação.
- `SPOTIFY_MODO=real`: OAuth de uma conta autorizada. Tokens ficam apenas em memória e expiram após duas horas.

Em respostas `429`, a API respeita `Retry-After` e tenta novamente até o limite configurado em `SPOTIFY_MAX_TENTATIVAS`.
