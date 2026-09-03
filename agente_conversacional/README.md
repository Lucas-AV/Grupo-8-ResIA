# Agente Conversacional — backend

Implementacao do backend do agente de recomendacao (Proposta B). Ver
[`docs/PIPELINE_AGENTE_PROPOSTA_B.md`](../docs/PIPELINE_AGENTE_PROPOSTA_B.md)
pra especificacao completa e
[`docs/BACKLOG_JIRA_PROPOSTA_B.md`](../docs/BACKLOG_JIRA_PROPOSTA_B.md) pro
backlog em tickets. Este README cobre só o que já existe: Épico 0
(infraestrutura de LLM).

## Setup

```bash
cd agente_conversacional
pip install -r requirements.txt
cp .env.example .env   # editar OLLAMA_MODEL / ANTHROPIC_API_KEY conforme necessário
```

## Rodar o backend

```bash
uvicorn app:app --reload
```

- `GET /health` — chama o LLM configurado com um prompt trivial e devolve
  `{"disponivel": bool, "backend": str, "erro": str|None}`. Nunca derruba o
  processo, mesmo com o LLM fora do ar (ticket 0.4).

## Testes

```bash
pytest
```

26 testes cobrindo o dispatcher `chamar_llm`, os dois backends (Ollama e
Claude) e o boot do FastAPI — todos com o LLM mockado, não dependem de
Ollama rodando de verdade.

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

`session_id` é aceito hoje como query param direto (não há cookie de
sessão ainda — depende do gerenciador de sessão do ticket 3.4, Épico 3).
Ajustar a assinatura de `/auth/login`/`/auth/logout` quando esse
gerenciador existir.

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

Módulo `recomendacao/` — carregamento/normalização, índice de
similaridade e a busca completa prontos; diversidade/cobertura (1.4)
segue em aberto.

| Ticket | O que cobre | Status |
|---|---|---|
| 1.1 — Carregar dataset e normalizar features de áudio | `recomendacao/dataset.py` — `carregar_dataset()` lê `data/dataset.csv` uma vez (cacheado com `functools.lru_cache`), marca `track_id_duplicado` sem remover linhas, e adiciona colunas `*_norm` com as 9 features de áudio contínuas padronizadas (z-score), preservando as colunas originais em escala crua pros filtros/buckets do ticket 1.3. | Feito |
| 1.2 — Índice de similaridade (k-NN / cosseno) | `recomendacao/indice.py` — `construir_indice()` monta, uma única vez (cacheado), a matriz de features normalizada linha a linha (norma L2); `IndiceSimilaridade.mais_similares(vetor_alvo, n)` devolve as `n` faixas mais próximas por cosseno via produto escalar vetorizado (numpy puro, sem nova dependência). Busca no dataset real (~31,8 mil faixas) roda em milissegundos, bem abaixo do limite de ~1s. | Feito |
| 1.3 — `buscar_recomendacoes(...)` completa | `recomendacao/busca.py` — assinatura completa (`genero`, `energia`, `valencia`, `dancabilidade`, `artista_referencia`, `excluir_explicit`, `n_resultados`, `perfil_usuario`, `faixas_ja_mostradas`); validação defensiva de cada campo (nunca levanta exceção); filtros rígidos (gênero, `excluir_explicit`, dedup de `track_id`) antes da similaridade; vetor-alvo pelos 3 casos (artista de referência → centróide, buckets categóricos, blend 70/30 com `perfil_usuario`); fallback por popularidade quando não há sinal nenhum; `n_resultados` sempre em `[1, 30]`. Ver decisões assumidas abaixo. | Feito |
| 1.4 — Cálculo de diversidade e cobertura | Depende de **1.3**. | Não iniciado |
| 1.5 — Testes unitários de `buscar_recomendacoes` | Depende de **1.4**. | Não iniciado |

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

Testes: `pytest` — 93 testes (69 anteriores + 24 do ticket 1.3), todos
sem depender de rede ou de serviços externos.
