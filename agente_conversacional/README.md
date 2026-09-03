# Agente Conversacional — backend

Implementação do backend do agente de recomendação (Proposta B). Ver
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
`detail.codigo = "sessao_invalida"`. Enquanto o pipeline do Épico 2 não for
integrado, `POST /chat` retorna `503` com
`detail.codigo = "pipeline_indisponivel"`; ele não usa catálogo demonstrativo
nem inventa recomendações.

O pipeline será conectado através de `TurnProcessor`. A fábrica
`create_app(session_store=..., turn_processor=...)` aceita dependências
opcionais para testes e para a integração com os Épicos 2 e 5.

## Testes

```bash
pytest
```

Os testes cobrem o dispatcher `chamar_llm`, os dois backends (Ollama e Claude),
o boot do FastAPI, sessões, expiração e os contratos HTTP do KAN-8. Todos usam
o LLM mockado e não dependem de Ollama rodando de verdade.

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
