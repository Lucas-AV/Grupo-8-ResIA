# Integração com a Spotify Web API

## O que é coletado

Após autorização OAuth, o sistema lê o perfil básico do usuário, suas top tracks e seus top artists nos períodos curto, médio ou longo. A coleta é limitada a 50 itens por chamada e registra o instante e a origem dos dados.

## Escopos e privacidade

| Escopo | Motivo |
| --- | --- |
| `user-top-read` | Top tracks e top artists para representar o perfil musical. |
| `user-read-private` | Perfil básico da conta. |

Tokens não aparecem no frontend, no LLM ou nos logs. O backend mantém o token em memória, associado a um cookie HTTP-only; encerrar a sessão remove esse registro.

## Atributos de áudio e catálogo local

O endpoint de atributos de áudio do Spotify foi removido/descontinuado. Para não depender dele, os atributos das top tracks são procurados no arquivo tratado do Spotify Tracks Dataset por `track_id`. Uma faixa ausente permanece sem atributos e é marcada com origem `indisponivel`; ela não recebe valores inventados.

## Modos de uso

`SPOTIFY_MODO=demo` é o padrão: disponibiliza três personas fictícias, sem login real e sem dados de pessoas. `SPOTIFY_MODO=real` usa `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET` e `SPOTIFY_REDIRECT_URI` definidos em `.env`; a URL deve ser idêntica à registrada no Spotify Developer Dashboard.

Em modo de desenvolvimento do Spotify, somente o proprietário Premium da aplicação e as contas permitidas podem autorizar. O modo demo permite a apresentação mesmo nessa restrição.

## Limites e falhas

Respostas `429` respeitam o cabeçalho `Retry-After` e são repetidas até `SPOTIFY_MAX_TENTATIVAS`. Erros de autorização, credenciais, conectividade e indisponibilidade do catálogo retornam mensagens estruturadas para a interface.

## GQ3 — estado atual

A análise de consistência das top tracks em clusters foi deixada como TODO no notebook obrigatório. Ela só será executada após a Fase 4, usando o mesmo scaler e modelo de clustering treinados: para cada uma das 2–3 personas/usuários autorizados, serão calculados cluster dominante, proporção dominante e entropia. Uma concentração de pelo menos 70% será o critério inicial de perfil concentrado. Dados Spotify não serão ingeridos para treino de modelo sem uma revisão de conformidade.
