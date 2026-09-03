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

| Ticket | O que cobre | Status |
|---|---|---|
| 5.1 — Registro do app | Variáveis `SPOTIFY_CLIENT_ID`/`SPOTIFY_CLIENT_SECRET`/`SPOTIFY_REDIRECT_URI` no `.env.example`, nunca hardcoded. Cadastro do app no Spotify Developer Dashboard ainda não feito (ação manual, fora do código). | Parcial — código pronto, falta cadastrar o app de verdade |
| 5.2 — `GET /auth/login` (PKCE) | `spotify_auth/pkce.py` + `spotify_auth/client.py` (`build_authorize_url`) — `state` e `code_challenge` (S256) gerados e correlacionados via `PendingAuth`. | Feito |
| 5.3 — `GET /auth/callback` | `spotify_auth/routes.py` — valida `state`, troca código por tokens, trata `?error=access_denied` (login cancelado) sem erro visível ao usuário. | Feito |
| 5.4 — Armazenamento/renovação de tokens | `spotify_auth/token_store.py` (SQLite + Fernet) e `client.get_valid_access_token` (renova quando falta <60s; se o refresh falhar, sessão cai pra anônima). | Feito |
| 5.5 — Busca do histórico | `spotify_auth/history.py` — top tracks, recently played, saved tracks (paginado). 429/timeout tratados como histórico parcial, não bloqueiam o login. | Feito |
| 5.6 — Matching com dataset local | Depende de **1.1** (dataset carregado em memória, Épico 1). | **Bloqueado — aguardando Épico 1** |
| 5.7 — Perfil de gosto (centróide) | Depende de **1.3** (`buscar_recomendacoes`, Épico 1). | **Bloqueado — aguardando Épico 1** |
| 5.8 — `POST /auth/logout` | `spotify_auth/routes.py` — descarta os tokens da sessão. | Feito |
| 5.9 — Casos de falha do OAuth | Tabela da seção 3.7 do pipeline coberta: `state` inválido, `error=access_denied`, refresh revogado, 429, timeout — todos testados com mocks (`test_spotify_client.py`, `test_spotify_history.py`, `test_spotify_routes.py`). | Feito |

Testes: `pytest` — 56 testes (26 do Épico 0 + 30 do Épico 5), todos com
rede mockada.
