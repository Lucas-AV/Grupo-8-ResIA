# Agente Conversacional — backend

Implementação do backend do agente de recomendação (Proposta B). Ver
[`docs/PIPELINE_AGENTE_PROPOSTA_B.md`](../docs/PIPELINE_AGENTE_PROPOSTA_B.md)
pra especificacao completa e
[`docs/BACKLOG_JIRA_PROPOSTA_B.md`](../docs/BACKLOG_JIRA_PROPOSTA_B.md) pro
backlog em tickets. Este README cobre o que já existe: infraestrutura de
LLM (Épico 0), motor de recomendação (Épico 1), pipeline conversacional
(Épico 2), sessões e API (KAN-8), integração Spotify OAuth (Épico 5) e
infra/qualidade do projeto (Épico 8). Só o frontend (Épico 4) ainda não
foi implementado. Para uma visão simples da entrega do KAN-8, veja
[`docs/KAN-8_BACKEND_API.md`](docs/KAN-8_BACKEND_API.md).

## Setup

Pré-requisito pro backend de LLM local (ticket 0.1): [Ollama](https://ollama.com)
instalado e o modelo baixado —

```bash
ollama pull qwen2.5:7b-instruct-q4_K_M
```

Backend em si:

```bash
cd agente_conversacional
pip install -r requirements.txt
cp .env.example .env
```

Edite o `.env` conforme necessário — os valores default já funcionam pro
Ollama local. Só mexa em:

- `LLM_BACKEND=claude` + `ANTHROPIC_API_KEY` se quiser o backend hospedado
  em vez do Ollama local (ticket 0.3).
- `SPOTIFY_CLIENT_ID`/`SPOTIFY_CLIENT_SECRET` se for testar o fluxo OAuth
  (registre o app em https://developer.spotify.com/dashboard primeiro,
  ticket 5.1) e `SPOTIFY_TOKEN_ENCRYPTION_KEY` (gere com o comando
  comentado no `.env.example`, ticket 5.4).
- `FRONTEND_URL` se o frontend (quando existir, Épico 4) rodar numa porta
  diferente de `5173` (ticket 8.2).

## Rodar o backend

```bash
uvicorn app:app --reload
```

- `GET /health` — chama o LLM configurado com um prompt trivial e devolve
  `{"disponivel": bool, "backend": str, "erro": str|None}`. Nunca derruba o
  processo, mesmo com o LLM fora do ar (ticket 0.4).
- `GET /auth/login`, `GET /auth/callback`, `POST /auth/logout` — fluxo
  OAuth do Spotify (Épico 5, ver seção abaixo).

Não há frontend ainda (Épico 4) — pra testar manualmente, use `curl` ou
abra as URLs acima direto no navegador.

## CORS (ticket 8.2)

Só a origem em `FRONTEND_URL` do `.env` (default `http://127.0.0.1:5173`)
tem acesso — nunca wildcard. Pra liberar mais de uma origem (ex.: dev +
demo), separe por vírgula: `FRONTEND_URL=http://127.0.0.1:5173,https://minha-demo.exemplo.com`.

## Tratamento de erro global (ticket 8.3)

Qualquer exceção não tratada em qualquer rota vira HTTP 500 com corpo
`{"erro": "erro interno do servidor"}` — nunca stack trace cru pro
cliente. O erro completo é logado no servidor (`logger.exception`, logger
`"agente"`).

## Rate limiting (ticket 8.4)

`rate_limit.py` tem um limitador em memória (`RateLimiter`, configurável
via `CHAT_RATE_LIMIT_MAX_REQUESTS`/`CHAT_RATE_LIMIT_WINDOW_SECONDS`) pronto
para ser ligado à rota de conversa em uma etapa posterior.

## API de sessões — KAN-8

O backend mantém sessões de conversa **em memória** para o MVP. Cada sessão é
criada com UUID4, expira após `SESSION_TIMEOUT_MINUTES` (30 minutos por padrão)
e é descartada no restart do processo. A expiração trata somente o histórico de
chat; a futura camada OAuth mantém os tokens em armazenamento separado.

- `POST /session` cria uma sessão e devolve `{"session_id": "<uuid4>"}`.
- `POST /chat` recebe `session_id` e `mensagem`; devolve texto, faixas e
  métricas no contrato consumido pelo frontend.
- `GET /chat/historico?session_id=...` devolve as mensagens auditáveis, com
  `role`, `conteudo`, `faixas_citadas` e timestamp UTC.

Sessões inexistentes ou expiradas retornam `404` com
`detail.codigo = "sessao_invalida"`. `POST /chat` está ligado ao pipeline
conversacional real (Épico 2, `chat/pipeline.py`) por padrão — só retorna
`503` com `detail.codigo = "pipeline_indisponivel"` se alguém injetar
explicitamente um `turn_processor` que sinalize indisponibilidade (ver
`chat.contracts.PipelineUnavailableError`), não é mais o comportamento
default.

O pipeline é conectado através de `TurnProcessor`
(`chat/contracts.py`). A fábrica `create_app(session_store=...,
turn_processor=...)` aceita dependências opcionais pra testes; sem
argumentos, usa `SessionStore()` e `ChatPipeline()` de verdade.

## Testes

```bash
python -m pytest
```

Os testes cobrem o dispatcher `chamar_llm`, os backends, o boot do FastAPI,
sessões, expiração, contratos HTTP do KAN-8, fluxo OAuth, CORS, tratamento de
erros e rate limiter. Todos usam LLM/Spotify mockados e não dependem de nada
rodando de verdade. A suíte roda
automaticamente em todo push/PR via
[`.github/workflows/agente-tests.yml`](../.github/workflows/agente-tests.yml)
(ticket 8.5).

## Camada de abstração `chamar_llm`

```python
from llm.client import chamar_llm

resposta = chamar_llm([{"role": "user", "content": "quero pagode"}])
```

- Backend selecionado por `LLM_BACKEND` (`ollama` por padrão, ou `claude`).
- `formato_json=True` pede resposta em JSON puro ao backend (usado pela
  extração estruturada, ticket 2.2).
- `timeout` em segundos; se omitido, usa `LLM_TIMEOUT_SECONDS` do `.env`
  (padrão 8s).
- Levanta `llm.errors.LLMCallError` em qualquer falha (rede, timeout,
  resposta malformada) ou `llm.client.LLMBackendNotConfigured` se
  `LLM_BACKEND` apontar pra um backend inexistente.

## Épico 0 — status por ticket

| Ticket | O que cobre | Status |
|---|---|---|
| 0.1 — Instalar/configurar modelo local | Ollama já instalado nesta máquina (v0.18.3); serviço estava parado, subiu ao rodar `ollama list`. Modelo alvo `qwen2.5:7b-instruct-q4_K_M` **ainda não foi baixado** — só há `glm-4.7-flash:latest` (19GB) local, usado pra validar o backend de ponta a ponta. Ver achado de RAM/GPU em [`docs/logistica_rede.md`](docs/logistica_rede.md). | Parcial — falta `ollama pull qwen2.5:7b-instruct-q4_K_M` e reteste com o modelo alvo |
| 0.2 — `chamar_llm(...)` | Implementado (`llm/client.py`), backend Ollama real (`llm/backends/ollama_backend.py`), testado com mocks e uma vez contra o Ollama real rodando localmente. | Feito |
| 0.3 — Backend hospedado alternativo | Implementado (`llm/backends/claude_backend.py`), troca via `LLM_BACKEND=claude`, chave lida de `ANTHROPIC_API_KEY`. Não testado contra a API real (precisa de chave válida). | Feito (não testado contra API real) |
| 0.4 — Health-check no boot | `app.py` usa `lifespan` do FastAPI pra logar disponibilidade no boot sem bloquear a subida; endpoint `GET /health` exposto. | Feito |
| 0.5 — Logística de rede da demo | Ver [`docs/logistica_rede.md`](docs/logistica_rede.md) — opção recomendada documentada, falta ensaiar no hardware real de quem apresenta. | Parcial — decisão proposta, falta validar/ensaiar |

## Épico 5 — Integração Spotify OAuth (status por ticket)

Módulo `spotify_auth/` — fluxo Authorization Code + PKCE, tokens
criptografados em SQLite (`cryptography.Fernet`), renovação proativa e
busca de histórico. Rotas montadas em `app.py`
(`GET /auth/login`, `GET /auth/callback`, `POST /auth/logout`).

`session_id` é aceito como query param direto (não há cookie de sessão).
Após o callback, o backend marca a sessão de conversa já existente como
autenticada; os tokens continuam guardados separadamente pelo OAuth. Nenhuma
segunda conversa é criada nesse processo.

**Desvio do fluxo descrito na seção 3.2 do pipeline:** `GET /auth/login`
não redireciona mais direto pro Spotify — devolve a página de
consentimento do ticket 5.10 primeiro. O redirect real (o que a seção
3.2 chama de passo 3) foi pra `GET /auth/login/start`. Motivo: o
Épico 4 (frontend) ainda não existe pra hospedar esse aviso antes do
botão "Conectar com Spotify", então o backend hospeda ele mesmo por
enquanto. Quando o Épico 4 existir, o frontend pode renderizar o texto
de `spotify_auth/consent.py` diretamente e chamar `/auth/login/start`
como o botão em si — nesse caso `GET /auth/login` volta a poder
redirecionar direto, se fizer mais sentido.

| Ticket | O que cobre | Status |
|---|---|---|
| 5.1 — Registro do app | Variáveis `SPOTIFY_CLIENT_ID`/`SPOTIFY_CLIENT_SECRET`/`SPOTIFY_REDIRECT_URI` no `.env.example`, nunca hardcoded. Cadastro do app no Spotify Developer Dashboard ainda não feito (ação manual, fora do código). | Parcial — código pronto, falta cadastrar o app de verdade |
| 5.2 — `GET /auth/login` (PKCE) | `spotify_auth/pkce.py` + `spotify_auth/client.py` (`build_authorize_url`), chamado por `GET /auth/login/start` — `state` e `code_challenge` (S256) gerados e correlacionados via `PendingAuth`. | Feito |
| 5.3 — `GET /auth/callback` | `spotify_auth/routes.py` — valida `state`, troca código por tokens, trata `?error=access_denied` (login cancelado) sem erro visível ao usuário. | Feito |
| 5.4 — Armazenamento/renovação de tokens | `spotify_auth/token_store.py` (SQLite + Fernet) e `client.get_valid_access_token` (renova quando falta <60s; se o refresh falhar, sessão cai pra anônima). | Feito |
| 5.5 — Busca do histórico | `spotify_auth/history.py` — top tracks, recently played, saved tracks (paginado). 429/timeout tratados como histórico parcial, não bloqueiam o login. | Feito |
| 5.6 — Matching com dataset local | 1.1 já está pronto (`recomendacao/dataset.py`); `recomendacao/normalizacao.py` (`normalizar_texto`) já existe pra reaproveitar aqui, conforme §3.5 do pipeline. | Desbloqueado — não iniciado |
| 5.7 — Perfil de gosto (centróide) | 1.3 já está pronto — `buscar_recomendacoes(perfil_usuario=...)` já aceita e faz o blend 70/30 (`recomendacao/busca.py`). Falta só calcular o centróide a partir do histórico casado (5.6) e injetar aqui. | Desbloqueado — não iniciado |
| 5.8 — `POST /auth/logout` | `spotify_auth/routes.py` — descarta os tokens da sessão. | Feito |
| 5.9 — Casos de falha do OAuth | Tabela da seção 3.7 do pipeline coberta: `state` inválido, `error=access_denied`, refresh revogado, 429, timeout — todos testados com mocks (`test_spotify_client.py`, `test_spotify_history.py`, `test_spotify_routes.py`). | Feito |
| 5.10 — Aviso de privacidade antes do login | `spotify_auth/consent.py` — `GET /auth/login` mostra os scopes lidos e a política de dados (§9 do pipeline) antes do link pra `/auth/login/start`. Implementado no backend por falta do Épico 4; ver desvio de fluxo acima. | Feito (via backend, adiantado do Épico 4) |

Testes: `pytest` — 57 testes (26 do Épico 0 + 31 do Épico 5), todos com
rede mockada.

## Épico 1 — Motor de recomendação (status por ticket)

Módulo `recomendacao/` — Épico 1 completo: carregamento/normalização,
índice de similaridade, busca completa, métricas de diversidade/
cobertura e a suíte formal de testes de edge cases.

| Ticket | O que cobre | Status |
|---|---|---|
| 1.1 — Carregar dataset e normalizar features de áudio | `recomendacao/dataset.py` — `carregar_dataset()` lê `data/dataset.csv` uma vez (cacheado com `functools.lru_cache`), marca `track_id_duplicado` sem remover linhas, e adiciona colunas `*_norm` com as 9 features de áudio contínuas padronizadas (z-score), preservando as colunas originais em escala crua pros filtros/buckets do ticket 1.3. | Feito |
| 1.2 — Índice de similaridade (k-NN / cosseno) | `recomendacao/indice.py` — `construir_indice()` monta, uma única vez (cacheado), a matriz de features normalizada linha a linha (norma L2); `IndiceSimilaridade.mais_similares(vetor_alvo, n)` devolve as `n` faixas mais próximas por cosseno via produto escalar vetorizado (numpy puro, sem nova dependência). Busca no dataset real (~31,8 mil faixas) roda em milissegundos, bem abaixo do limite de ~1s. | Feito |
| 1.3 — `buscar_recomendacoes(...)` completa | `recomendacao/busca.py` — assinatura completa (`genero`, `energia`, `valencia`, `dancabilidade`, `artista_referencia`, `excluir_explicit`, `n_resultados`, `perfil_usuario`, `faixas_ja_mostradas`); validação defensiva de cada campo (nunca levanta exceção); filtros rígidos (gênero, `excluir_explicit`, dedup de `track_id`) antes da similaridade; vetor-alvo pelos 3 casos (artista de referência → centróide, buckets categóricos, blend 70/30 com `perfil_usuario`); fallback por popularidade quando não há sinal nenhum; `n_resultados` sempre em `[1, 30]`. Ver decisões assumidas abaixo. | Feito |
| 1.4 — Cálculo de diversidade e cobertura | `diversidade_generos` (nº de gêneros distintos no resultado) e `cobertura_sessao` (proporção de faixas cujo `track_id` não está em `faixas_ja_mostradas`) calculados dentro de `buscar_recomendacoes` e sempre presentes na resposta — inclusive no fallback de popularidade e no caso de resultado vazio (`0` e `0.0`, respectivamente). | Feito |
| 1.5 — Testes unitários de `buscar_recomendacoes` | `test_recomendacoes_edge_cases.py` fecha as combinações que faltavam contra a tabela de edge cases (§7 do pipeline) e os critérios do ticket: atributo só (dançabilidade, valência — energia já estava em 1.3), gênero/artista inválido em combinação, dedup na busca por similaridade (não só no fallback), e resultado vazio nos dois caminhos (fallback e similaridade). O resto dos critérios (combinação de sinal, `n_resultados` fora da faixa, gênero/artista inválido isolado, dedup no fallback) já tinha saído coberto organicamente em 1.3/1.4. | Feito |

**Decisões assumidas no 1.3** (a especificação detalhada referenciada
pelo ticket — filtros/buckets/blend — não está mais no
`PIPELINE_AGENTE_PROPOSTA_B.md` atual; só o texto do próprio ticket do
Jira tinha esse nível de detalhe). Vale o time confirmar:

- Buckets `baixa`/`media`/`alta` (e `triste`/`neutro`/`feliz` pra
  valência) mapeiam pra -1/0/+1 desvio-padrão na dimensão normalizada
  correspondente — não havia threshold explícito especificado.
- Quando `artista_referencia` bate com o dataset, o centróide é
  calculado sobre a base inteira (não restrito ao `genero` do filtro) —
  representa o "perfil de som" do artista, independente de gênero.
- Blend 70/30 é sempre `0.7 * vetor_da_consulta + 0.3 * perfil_usuario`
  (perfil como viés secundário, nunca dominante) — quando não há nenhum
  outro sinal (nem artista, nem bucket), `perfil_usuario` sozinho vira o
  vetor-alvo (100%, sem blend).
- `faixas_ja_mostradas` é aceito e validado na assinatura, mas não filtra
  resultado nesta função — só o ticket 1.4 (`cobertura_sessao`) usa esse
  parâmetro de fato.
- Faixas do próprio artista de referência não são excluídas do
  resultado (nada no ticket pedia isso).
- `cobertura_sessao` com resultado vazio (nenhum candidato passou nos
  filtros) devolve `0.0` em vez de indefinido/`NaN` — evita dividir por
  zero sem esconder que não há faixas novas nem antigas, simplesmente
  não há faixas.

Testes: `pytest` — 109 testes (103 anteriores + 6 do ticket 1.5), todos
sem depender de rede ou de serviços externos. Épico 1 completo.

## Épico 2 — Pipeline conversacional (status por ticket)

Módulo `chat/` — roteador determinístico, extração e geração via LLM,
validação de schema, template determinístico, auditoria mecânica de
citações e o orquestrador (`chat/pipeline.py::ChatPipeline`) que
implementa `TurnProcessor` e está ligado em `app.py` por padrão.

| Ticket | O que cobre | Status |
|---|---|---|
| 2.1 — Roteador determinístico por regex | `chat/roteador.py` — reconhece os 32 gêneros reais de `track_genre` do dataset (sinônimos PT/EN), humor/energia/valência/dançabilidade e intensificadores ("mais animado", "mais calmo"...), além de saudações e pedidos fora de escopo (letra de música, compor música) como padrões próprios. Só resolve "pedidos simples" (até 6 palavras) — frases livres/longas (caso de uso 2) são deixadas de propósito pra extração via LLM. | Feito |
| 2.2 — Extração via LLM | `chat/extrator.py` — prompt de sistema versionado (`SYSTEM_PROMPT_EXTRACAO_V1`), usa o timeout padrão de `chamar_llm` (~8s), parser tolerante a texto/markdown ao redor do JSON (`chat/json_extrator.py`). | Feito |
| 2.3 — Validador de schema | `chat/validador.py` — campo fora do domínio vira `null` sem rejeitar a consulta inteira; `genero` validado contra `track_genre` real; `artista_referencia` normalizado com a mesma `normalizar_texto` do matching OAuth (5.6); `n_resultados` sempre em `[1, 30]`. | Feito |
| 2.4 — Resposta por template determinístico | `chat/template.py` — texto fixo pro resultado com faixas e pro resultado vazio, sem LLM; também cobre saudação, fora de escopo e a pergunta de esclarecimento do fallback total. | Feito |
| 2.5 — Geração via LLM | `chat/gerador.py` — segunda chamada ao LLM (prompt `SYSTEM_PROMPT_GERACAO_V1`) pede JSON `{"texto", "faixas_citadas"}`; resultado vazio nunca aciona o LLM; qualquer falha (timeout, indisponibilidade, JSON inválido/sem texto) cai pro template (2.4) sem quebrar o turno. | Feito |
| 2.6 — Auditoria mecânica de `faixas_citadas` | `chat/auditoria.py` — compara `faixas_citadas` com os `track_id`s reais do resultado da busca daquele turno; citação divergente é filtrada do resultado final e logada como warning (`agente.chat.auditoria`). | Feito |
| 2.7 — Fallback total | Implementado dentro de `chat/pipeline.py::ChatPipeline.process` — roteador sem match + extração retornando `None` cai direto na pergunta de esclarecimento (2.4), sem chamar `buscar_recomendacoes`. | Feito |
| 2.8 — Truncamento do histórico enviado ao LLM | `chat/historico_llm.py` (`LIMITE_HISTORICO_LLM = 6`) — usado pela extração (2.2) e pela geração (2.5); `GET /chat/historico` continua devolvendo o histórico completo da sessão. | Feito |

**Gaps conhecidos, fora do escopo estrito dos critérios de aceite dos
tickets 2.1–2.8:**

- Caso de uso 8 ("por que vocês recomendaram isso?") não tem tratamento
  especial — `consulta_efetiva` não é persistida por mensagem no
  histórico da sessão (`sessions/models.py::Message` só guarda
  `faixas_citadas`), então não há hoje como reconstruir os filtros do
  turno anterior pra responder essa pergunta sem uma nova busca. Ficaria
  pra uma iteração futura que estenda `Message`/`SessionStore`.
- Caso de uso 6 (artista pedido não existe no dataset): o comportamento
  técnico é correto (`busca.py` degrada pra `None`/outros filtros/
  popularidade, nunca inventa faixa), mas a resposta não menciona
  explicitamente "esse artista não está na nossa base" — usa o mesmo
  texto genérico de resultado vazio/com resultado do template (2.4) ou o
  texto livre da geração (2.5), que pode ou não mencionar isso dependendo
  do que o LLM escrever.
- O roteador (2.1) cobre os gêneros **reais** do dataset carregado neste
  repositório (`data/dataset.csv`, 32 gêneros de `acoustic` a `electro` —
  um recorte alfabético do dataset completo do Kaggle). Exemplos do
  próprio backlog como "pagode"/"sertanejo" não existem nesse recorte;
  o roteador não tem sinônimo pra eles (cai pra extração via LLM, que
  também não vai achar o gênero — `buscar_recomendacoes` degrada pra
  filtros/popularidade sem esse gênero, não quebra).

Testes: `pytest` — 74 testes novos (roteador, extração, validador,
template, geração, auditoria, orquestrador do pipeline e o turno
completo via API real em `test_chat_endpoint.py`), todos com LLM e
dataset mockados. Suíte completa do backend: 242 testes.

## Épico 8 — Infraestrutura de projeto, qualidade e deploy (status por ticket)

| Ticket | O que cobre | Status |
|---|---|---|
| 8.1 — Scaffold do backend | Já existia como subproduto dos Épicos 0/5 — `app.py` como entrypoint, `requirements.txt` (instala limpo, testado), `.env.example` cobrindo 0.x/5.x/8.x. Backend sobe com `uvicorn app:app --reload`. | Feito |
| 8.2 — CORS | `app.py` (`CORSMiddleware`), origem(ns) via `FRONTEND_URL` (nunca wildcard). Testado em `test_cors.py`. | Feito |
| 8.3 — Handler de erro global | `app.py` (`handle_unhandled_exception`) — qualquer exceção não tratada vira HTTP 500 padronizado, nunca stack trace cru; log completo no servidor. Testado em `test_error_handler.py`. | Feito |
| 8.4 — Rate limiting no `/chat` | `rate_limit.py` (`RateLimiter`) está pronto e testado (`test_rate_limit.py`). A rota `POST /chat` já existe pelo KAN-8; falta somente ligar o limitador nela no ticket 8.4. | **Pendente — integração específica do ticket 8.4** |
| 8.5 — CI de testes (pytest) | [`.github/workflows/agente-tests.yml`](../.github/workflows/agente-tests.yml) — roda `pytest` em todo push/PR que toque `agente_conversacional/`. Cobre 1.5/2.9 automaticamente assim que esses testes existirem (descoberta automática do pytest). | Feito |
| 8.6 — README / guia de setup | Este arquivo — Ollama, `.env`, CORS, erro global, rate limiter, testes, tabelas de status por épico. | Feito |
| 8.7 — Deploy/hosting real | Depende de **3.2** e **4.1** (Épicos 3 e 4, nenhum implementado ainda) — sem backend orquestrado nem frontend, não há o que publicar. | **Bloqueado — aguardando Épicos 3 e 4** |

Testes: `pytest` — 67 testes no total (26 do Épico 0 + 31 do Épico 5 + 10
do Épico 8), todos com rede mockada.
