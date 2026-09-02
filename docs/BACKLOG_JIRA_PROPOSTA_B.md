# Backlog Técnico — Insumo para Kanban Jira (Proposta B)

Grupo 8 · Residência em IA (UnB / LabLivre / Instituto Eldorado) · Nano-Challenge CBL
Setembro de 2026

> Confirmação de escopo: o time segue com a **Proposta B** — LLM interage
> com o motor de busca em Python via um pipeline em etapas (roteador →
> extração → validação → `buscar_recomendacoes` → geração), nunca por
> tool-calling nativo. A Proposta C (reforço por feedback) **não** está
> incluída neste backlog.
>
> Este documento não define nada de novo — é a mesma arquitetura já
> especificada em `PROPOSTAS_AGENTE_CONVERSACIONAL.md` e
> [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md),
> reorganizada em tickets prontos pra virar cards no Jira. Cada ticket tem
> descrição, critérios de aceite, dependências e referência à seção
> técnica onde o "como fazer" já está detalhado.

## 0. Como usar este documento

- **1 Épico do Jira por seção** `## Épico N` abaixo.
- **1 card do Jira por ticket** (`### N.M — Título`) — copiar título +
  descrição + critérios de aceite direto pro campo do card.
- **Prioridade** (`P0`/`P1`/`P2`) — sugestão de coluna/ordem no backlog,
  não um campo obrigatório do Jira: `P0` é o que precisa estar pronto pra
  qualquer demo minimamente funcional existir; `P1` deixa a experiência
  completa; `P2` é o que corta primeiro se faltar tempo.
- **Tamanho** (`P`/`M`/`G`) — estimativa grosseira (pequeno/médio/grande),
  não pontos de história calibrados — o time pode recalibrar na primeira
  reunião de planejamento.
- **Depende de** — outros tickets que precisam estar concluídos antes.
  Use isso pra montar a ordem das colunas "To Do" no kanban, não só uma
  lista plana.

### 0.1 Ordem sugerida (sprint único de ~5-6 dias)

| Dia | Foco |
|---|---|
| 1 | Épico 0 (infra LLM) + Épico 1 (motor de recomendação) — nada de conversa ainda, só a base determinística |
| 2 | Épico 2 tickets `P0` (roteador + extração + validação + resposta por template) + Épico 3 — já dá pra ter um MVP conversando, sem geração solta de texto nem login |
| 3 | Épico 4 tickets `P0`/`P1` (frontend do chat) + Épico 7 tickets `P0` — testar o MVP de ponta a ponta |
| 4 | Épico 2 tickets `P1` (geração via LLM) + Épico 5 (OAuth completo) |
| 5 | Épico 6 + Épico 7 tickets restantes — observabilidade, testes de edge case, ensaio de demo |
| 6 (se houver) | Buffer — tickets `P2` que sobraram, polimento |

---

## Épico 0 — Infraestrutura de LLM

### 0.1 — Instalar e configurar o modelo local `[P0]` `[P]`

**Área:** Infra
**Descrição:** Instalar Ollama no computador que vai servir o modelo
durante a demo; baixar `qwen2.5:7b-instruct-q4_K_M`; validar que responde
via `curl http://localhost:11434/api/chat`.

**Critérios de aceite:**
- [ ] Ollama rodando e respondendo localmente.
- [ ] Modelo baixado e testado com um prompt simples.
- [ ] Anotado quanto de RAM/VRAM o processo consome de fato, pra
      confirmar que o hardware do colega aguenta.

**Depende de:** —
**Referência:** `PROPOSTAS_AGENTE_CONVERSACIONAL.md` §1.1

### 0.2 — Camada de abstração `chamar_llm(...)` `[P0]` `[M]`

**Área:** Backend
**Descrição:** Implementar a função única que qualquer parte do pipeline
usa pra falar com o LLM, com o backend Ollama por trás (via HTTP).

**Critérios de aceite:**
- [ ] Assinatura `chamar_llm(mensagens, formato_json=None) -> resposta`.
- [ ] Backend selecionável por variável de ambiente (`LLM_BACKEND=ollama`
      já funcionando; outros valores podem ficar como stub por enquanto).
- [ ] Timeout configurável na chamada (usado pelos tickets 2.2 e 2.5).

**Depende de:** 0.1
**Referência:** `PROPOSTAS_AGENTE_CONVERSACIONAL.md` §1.3

### 0.3 — Backend de LLM hospedado alternativo `[P1]` `[M]`

**Área:** Backend
**Descrição:** Implementar um segundo backend (Claude API ou Groq) atrás
da mesma interface de 0.2, selecionável pela mesma variável de ambiente —
plano B se o modelo local falhar perto da apresentação.

**Critérios de aceite:**
- [ ] Troca de `LLM_BACKEND=ollama` para `LLM_BACKEND=claude` (ou `groq`)
      sem mudar nenhum código do pipeline.
- [ ] Chave de API lida de variável de ambiente, nunca hardcoded.

**Depende de:** 0.2
**Referência:** `PROPOSTAS_AGENTE_CONVERSACIONAL.md` §1.2, §1.3

### 0.4 — Health-check do LLM no boot do backend `[P1]` `[P]`

**Área:** Backend
**Descrição:** No início do backend, fazer uma chamada trivial via
`chamar_llm` e logar se está disponível — sem bloquear a subida do
servidor se não estiver.

**Critérios de aceite:**
- [ ] Backend sobe normalmente mesmo com o LLM fora do ar.
- [ ] Log claro indicando disponibilidade do LLM no boot.

**Depende de:** 0.2
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §2.1

### 0.5 — Definir e testar a logística de rede da demo `[P0]` `[P]`

**Área:** Infra
**Descrição:** Decidir entre as três opções (mesma Wi-Fi / túnel público
/ tudo na mesma máquina) e testar de verdade antes do dia da
apresentação.

**Critérios de aceite:**
- [ ] Opção escolhida documentada.
- [ ] Testada uma vez de ponta a ponta na configuração real (não só em
      localhost).

**Depende de:** 0.1
**Referência:** `PROPOSTAS_AGENTE_CONVERSACIONAL.md` §1.1

---

## Épico 1 — Motor de recomendação

### 1.1 — Carregar dataset e normalizar features de áudio `[P0]` `[M]`

**Área:** Dados
**Descrição:** Carregar `dataset.csv` inteiro em memória (DataFrame) no
boot do backend e normalizar as colunas de features de áudio usadas no
cálculo de similaridade.

**Critérios de aceite:**
- [ ] Dataset carregado uma única vez no boot, não a cada busca.
- [ ] Colunas numéricas padronizadas antes de qualquer cálculo de
      distância.
- [ ] Duplicatas de `track_id` identificadas (não removidas do dataset,
      só marcadas/deduplicadas na hora da busca — ver 1.3).

**Depende de:** —
**Referência:** explicação da normalização na conversa técnica sobre o
motor de recomendação; [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §2.1

### 1.2 — Índice de similaridade (k-NN / cosseno) `[P0]` `[M]`

**Área:** Dados
**Descrição:** Construir a estrutura usada pra calcular similaridade de
cosseno entre um vetor-alvo e as faixas do dataset, uma vez no boot.

**Critérios de aceite:**
- [ ] Cálculo de similaridade não recalcula normalização a cada chamada.
- [ ] Tempo de resposta de uma busca fica abaixo de ~1s no hardware de
      teste (ajustar conforme necessário).

**Depende de:** 1.1
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §4.2.5

### 1.3 — Implementar `buscar_recomendacoes(...)` completa `[P0]` `[G]`

**Área:** Dados/Backend
**Descrição:** Implementar a função com a assinatura, validação
defensiva, filtros rígidos, montagem de vetor-alvo, ranking e fallback de
popularidade já especificados.

**Critérios de aceite:**
- [ ] Assinatura idêntica à especificada (todos os parâmetros, incluindo
      `faixas_ja_mostradas`).
- [ ] Validação defensiva de cada parâmetro (nunca quebra com entrada
      inválida — degrada pro comportamento padrão documentado).
- [ ] Filtros rígidos aplicados antes do cálculo de similaridade (gênero,
      `excluir_explicit`, dedup de faixa).
- [ ] Vetor-alvo montado corretamente pros três casos: artista de
      referência (centróide), atributos categóricos (buckets), e blend
      70/30 com `perfil_usuario` quando presente.
- [ ] Fallback de popularidade geral quando nenhum sinal é informado.
- [ ] `n_resultados` sempre limitado entre 1 e 30, mesmo se pedido fora
      da faixa.

**Depende de:** 1.2
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §4.2 (todas as
subseções — é a especificação completa da função)

### 1.4 — Cálculo de diversidade e cobertura `[P0]` `[P]`

**Área:** Dados
**Descrição:** Dentro de `buscar_recomendacoes`, calcular
`diversidade_generos` e `cobertura_sessao` a partir do resultado final e
de `faixas_ja_mostradas`.

**Critérios de aceite:**
- [ ] `diversidade_generos` = contagem de gêneros distintos no resultado.
- [ ] `cobertura_sessao` = proporção de faixas cujo `track_id` não está
      em `faixas_ja_mostradas`.
- [ ] Os dois valores sempre presentes na resposta, mesmo quando o
      resultado vem do fallback de popularidade.

**Depende de:** 1.3
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §2.3, §4.2.5
(passo 8), §4.2.6

### 1.5 — Testes unitários de `buscar_recomendacoes` `[P1]` `[M]`

**Área:** QA/Dados
**Descrição:** Cobrir com testes automatizados os casos de uso e edge
cases já documentados que dizem respeito à função (não ao pipeline
conversacional inteiro).

**Critérios de aceite:**
- [ ] Teste pra cada combinação de sinal (gênero só, atributo só, artista
      de referência, nenhum sinal).
- [ ] Teste de `n_resultados` fora da faixa válida.
- [ ] Teste de gênero/artista inválido (deve virar `None`, não quebrar).
- [ ] Teste de dataset com `track_id` duplicado não aparecendo duas vezes
      no mesmo resultado.

**Depende de:** 1.4
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §7 (tabela de
edge cases)

---

## Épico 2 — Pipeline conversacional (turno de chat)

### 2.1 — Roteador determinístico por regex `[P0]` `[M]`

**Área:** Backend
**Descrição:** Implementar o conjunto de regras/padrões que reconhece
pedidos simples (sinônimos de gênero, humor, intensificadores como "mais
animado") sem precisar do LLM.

**Critérios de aceite:**
- [ ] Lista inicial de padrões cobrindo pelo menos os gêneros mais comuns
      do dataset e os termos de humor/energia usados nos exemplos já
      documentados.
- [ ] Quando reconhece, monta a consulta estruturada completa sem chamar
      `chamar_llm`.
- [ ] Reconhece saudações/small talk como um padrão próprio (não vira
      busca).

**Depende de:** —
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §5 (passo 3),
§6 (caso de uso 9)

### 2.2 — Etapa de extração via LLM `[P0]` `[M]`

**Área:** Backend
**Descrição:** Quando o roteador não resolve, chamar o LLM com um prompt
restrito pedindo só o JSON da consulta estruturada.

**Critérios de aceite:**
- [ ] Prompt de sistema definido e versionado (arquivo/constante, não
      hardcoded solto no meio do código).
- [ ] Timeout curto configurado (ex.: 8s).
- [ ] Parser tolera texto extra ao redor do JSON (extrai o primeiro bloco
      `{...}` válido) antes de desistir.

**Depende de:** 0.2, 2.1
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §4.2.1, §5
(passo 4), §7 (edge case "LLM devolve texto ao redor do JSON")

### 2.3 — Validador de schema da consulta estruturada `[P0]` `[P]`

**Área:** Backend
**Descrição:** Validar a consulta (vinda do roteador ou da extração)
contra o schema fixo antes de chamar `buscar_recomendacoes`.

**Critérios de aceite:**
- [ ] Campo fora do domínio esperado vira `null`, nunca rejeita a
      consulta inteira.
- [ ] `genero` validado contra a lista real de `track_genre` do dataset.
- [ ] `artista_referencia` normalizado (mesma função de normalização
      usada no matching de OAuth, ticket 5.6).

**Depende de:** 1.1, 2.2
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §4.2.1

### 2.4 — Resposta por template determinístico `[P0]` `[P]`

**Área:** Backend
**Descrição:** Formatar o resultado de `buscar_recomendacoes` em texto
fixo (sem LLM) — é a resposta padrão do MVP antes do ticket 2.5 existir,
e o fallback permanente quando o LLM de geração está indisponível.

**Critérios de aceite:**
- [ ] Template cobre resultado com faixas e resultado vazio (zero faixas
      encontradas) de forma diferenciada.
- [ ] Não depende de nenhuma chamada de LLM.

**Depende de:** 1.3
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §5 (passo 7),
§11

### 2.5 — Etapa de geração via LLM `[P1]` `[M]`

**Área:** Backend
**Descrição:** Segunda chamada ao LLM, que transforma o resultado de
`buscar_recomendacoes` numa resposta em linguagem natural, citando só as
faixas retornadas.

**Critérios de aceite:**
- [ ] Prompt de sistema instrui explicitamente a nunca citar faixa fora
      da lista recebida.
- [ ] Resposta preenche `faixas_citadas` com os `track_id`s realmente
      usados no texto.
- [ ] Se o LLM falhar/timeout nesta etapa, cai pro template (2.4) sem
      quebrar o turno.

**Depende de:** 0.2, 1.3, 2.4
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §5 (passo 7),
§4.3

### 2.6 — Auditoria mecânica de `faixas_citadas` `[P1]` `[P]`

**Área:** Backend/QA
**Descrição:** Checagem automática (não só instrução de prompt) de que
toda faixa citada no texto da resposta corresponde a um `track_id` que
veio de verdade do resultado de `buscar_recomendacoes` daquele turno.

**Critérios de aceite:**
- [ ] Função/teste que compara `faixas_citadas` da resposta com os
      `track_id`s do resultado real e sinaliza divergência.
- [ ] Divergência é logada (não precisa bloquear a resposta no MVP, mas
      precisa ser visível).

**Depende de:** 2.5
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §4.3, §7
(edge case de manipulação de prompt)

### 2.7 — Fallback total (roteador + LLM indisponíveis) `[P0]` `[P]`

**Área:** Backend
**Descrição:** Quando o roteador não reconhece e a extração via LLM
falha ou está indisponível, responder com uma pergunta de esclarecimento
por template, sem chamar `buscar_recomendacoes`.

**Critérios de aceite:**
- [ ] Nunca chama `buscar_recomendacoes` com consulta vazia.
- [ ] Resposta de esclarecimento é genérica, mas não um erro cru pro
      usuário.

**Depende de:** 2.1, 2.2
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §5 (passo 8)

### 2.8 — Truncamento do histórico enviado ao LLM `[P2]` `[P]`

**Área:** Backend
**Descrição:** Limitar quantas mensagens do histórico da sessão são
enviadas nas chamadas de extração/geração (ex.: últimas 6), mesmo que o
histórico completo continue guardado pra UI.

**Critérios de aceite:**
- [ ] Histórico enviado ao LLM nunca ultrapassa o limite configurado.
- [ ] Histórico completo da sessão continua disponível via
      `GET /chat/historico` (ticket 3.3).

**Depende de:** 2.2, 3.4
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §7 (edge case
de contexto longo)

---

## Épico 3 — Backend / API

### 3.1 — Endpoint `POST /session` `[P0]` `[P]`

**Área:** Backend
**Descrição:** Cria uma sessão anônima nova e devolve `session_id`.

**Critérios de aceite:**
- [ ] `session_id` gerado de forma não previsível (UUID ou equivalente).
- [ ] Sessão inicializada com histórico vazio e `perfil_usuario=None`.

**Depende de:** —
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §4.1, §2.2

### 3.2 — Endpoint `POST /chat` (orquestração do turno) `[P0]` `[G]`

**Área:** Backend
**Descrição:** Endpoint que recebe a mensagem do usuário e executa o
pipeline completo (2.1 → 2.7), montando a resposta final.

**Critérios de aceite:**
- [ ] Segue exatamente a ordem de decisão do fluxograma da seção 5.1 do
      pipeline.
- [ ] Atualiza o histórico da sessão e as métricas acumuladas ao final de
      cada turno.
- [ ] Resposta inclui texto final + lista estruturada de faixas.

**Depende de:** 2.1, 2.3, 2.4, 2.7, 3.1, 3.4
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §5.1, §5.2

### 3.3 — Endpoint `GET /chat/historico` `[P1]` `[P]`

**Área:** Backend
**Descrição:** Devolve o histórico de mensagens da sessão, pra recarregar
a UI depois de um refresh de página.

**Critérios de aceite:**
- [ ] Formato de mensagem consistente com o especificado (seção 4.3 do
      pipeline).

**Depende de:** 3.4
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §4.1, §4.3

### 3.4 — Gerenciador de sessão `[P0]` `[M]`

**Área:** Backend
**Descrição:** Estrutura em memória (dict) ou SQLite guardando, por
`session_id`: histórico de mensagens, `perfil_usuario`, faixas já
mostradas, métricas acumuladas de diversidade/cobertura.

**Critérios de aceite:**
- [ ] Sessão inválida/inexistente é tratada sem quebrar o backend (ver
      ticket 7.2).
- [ ] Estrutura pronta pra ser lida/escrita pelos tickets 3.1, 3.2, 3.3.

**Depende de:** —
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §2.5

### 3.5 — Timeout de inatividade da sessão `[P2]` `[P]`

**Área:** Backend
**Descrição:** Expirar sessões inativas há mais de ~30 minutos,
descartando o histórico de chat (tokens OAuth, se houver, não são
afetados).

**Critérios de aceite:**
- [ ] Sessão expirada não aparece mais em `GET /chat/historico`.
- [ ] Tokens OAuth associados permanecem intactos após expiração da
      sessão de chat.

**Depende de:** 3.4, 5.4
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §2.4

---

## Épico 4 — Frontend

### 4.1 — Tela de chat (input + histórico) `[P0]` `[G]`

**Área:** Frontend
**Descrição:** Interface principal — campo de mensagem, lista de
mensagens trocadas, chamada ao `POST /chat`.

**Critérios de aceite:**
- [ ] Envia mensagem e exibe a resposta do agente.
- [ ] Mantém o `session_id` entre mensagens (cookie/localStorage).

**Depende de:** 3.1, 3.2
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §1.3
(fronteiras de responsabilidade: frontend só fala com o backend)

### 4.2 — Cards de faixa a partir da lista estruturada `[P0]` `[M]`

**Área:** Frontend
**Descrição:** Renderizar as faixas retornadas (não só o texto) como
cards — nome, artista, álbum, gênero.

**Critérios de aceite:**
- [ ] Cards montados a partir do campo `faixas` da resposta, não fazendo
      parsing do texto livre.

**Depende de:** 4.1
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §5 (passo 10)

### 4.3 — Indicador de "processando" `[P1]` `[P]`

**Área:** Frontend
**Descrição:** Feedback visual enquanto o backend processa o turno —
importante com modelo local, que pode demorar mais que uma API na nuvem.

**Critérios de aceite:**
- [ ] Indicador aparece a partir do envio e some quando a resposta chega.

**Depende de:** 4.1
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §7 (edge case
de sessões concorrentes no mesmo Ollama)

### 4.4 — Botão de login com Spotify e estado autenticado `[P1]` `[M]`

**Área:** Frontend
**Descrição:** Botão que inicia o fluxo redirecionando pra
`GET /auth/login`; UI reflete quando a sessão está autenticada.

**Critérios de aceite:**
- [ ] Estado da UI muda visivelmente após login concluído.
- [ ] Histórico de chat existente antes do login não é perdido (sessão
      promovida, não recriada).

**Depende de:** 5.2, 5.3
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §2.2, §6
(caso de uso 11)

### 4.5 — Fluxo de logout `[P2]` `[P]`

**Área:** Frontend
**Descrição:** Botão de logout chamando `POST /auth/logout`.

**Critérios de aceite:**
- [ ] Após logout, UI volta ao estado anônimo.
- [ ] Histórico de chat da conversa atual permanece visível (só os
      tokens somem, ver seção 2.4 do pipeline).

**Depende de:** 5.8
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §2.4, §6
(caso de uso 12)

---

## Épico 5 — Integração Spotify OAuth

### 5.1 — Registro do app no Spotify Developer Dashboard `[P1]` `[P]`

**Área:** Infra
**Descrição:** Criar o app, anotar `client_id`/`client_secret`, registrar
a `redirect_uri` de desenvolvimento/demo.

**Critérios de aceite:**
- [ ] Credenciais salvas como variável de ambiente, nunca commitadas.

**Depende de:** —
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §3.1

### 5.2 — Endpoint `GET /auth/login` (PKCE) `[P1]` `[M]`

**Área:** Backend
**Descrição:** Gera `code_verifier`/`code_challenge` (PKCE) e `state`
anti-CSRF, redireciona pro Spotify com os scopes necessários.

**Critérios de aceite:**
- [ ] Scopes: `user-top-read`, `user-read-recently-played`,
      `user-library-read` — nenhum scope de escrita/player.
- [ ] `state` gerado e associado à sessão antes do redirect.

**Depende de:** 5.1
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §3.2

### 5.3 — Endpoint `GET /auth/callback` `[P1]` `[M]`

**Área:** Backend
**Descrição:** Recebe o retorno do Spotify, valida `state`, troca `code`
por `access_token`/`refresh_token`.

**Critérios de aceite:**
- [ ] `state` inválido é rejeitado sem trocar o código.
- [ ] `?error=access_denied` (usuário negou) tratado sem erro visível ao
      usuário — sessão permanece anônima.

**Depende de:** 5.2
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §3.2, §3.7

### 5.4 — Armazenamento e renovação automática de tokens `[P1]` `[M]`

**Área:** Backend
**Descrição:** Guardar tokens criptografados; renovar `access_token`
proativamente antes de expirar.

**Critérios de aceite:**
- [ ] Tokens nunca em texto puro no armazenamento nem em log.
- [ ] Renovação acontece antes de chamadas à API do Spotify quando o
      token está perto de expirar (ex.: <60s de validade).

**Depende de:** 5.3
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §3.3, §9

### 5.5 — Busca do histórico do usuário `[P1]` `[M]`

**Área:** Backend
**Descrição:** Chamar `/me/top/tracks`, `/me/player/recently-played` e
`/me/tracks` após login.

**Critérios de aceite:**
- [ ] Rate limit (HTTP 429) tratado sem travar o login (perfil fica
      vazio dessa vez, não impede a sessão de ficar autenticada).

**Depende de:** 5.4
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §3.4, §3.7

### 5.6 — Matching do histórico com o dataset local `[P1]` `[M]`

**Área:** Dados/Backend
**Descrição:** Casar as faixas do histórico com o dataset por `track_id`
exato e, se não bater, por nome normalizado de faixa + artista.

**Critérios de aceite:**
- [ ] Normalização (lowercase, sem acento/pontuação) compartilhada com a
      normalização de `artista_referencia` (ticket 2.3).
- [ ] Taxa de cobertura do match calculada e logada.

**Depende de:** 1.1, 5.5
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §3.5

### 5.7 — Perfil de gosto (centróide) e injeção em `buscar_recomendacoes` `[P1]` `[M]`

**Área:** Dados/Backend
**Descrição:** Calcular o centróide das features das faixas casadas e
passar como `perfil_usuario` nas chamadas de `buscar_recomendacoes` da
sessão.

**Critérios de aceite:**
- [ ] Cobertura zero (nenhuma faixa casada) resulta em `perfil_usuario`
      vazio, sem erro — comportamento idêntico ao anônimo.

**Depende de:** 1.3, 5.6
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §3.6

### 5.8 — Endpoint `POST /auth/logout` `[P2]` `[P]`

**Área:** Backend
**Descrição:** Descarta os tokens da sessão; sessão volta a anônima.

**Critérios de aceite:**
- [ ] Histórico de chat da sessão atual não é apagado, só os tokens.

**Depende de:** 5.4
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §2.4

### 5.9 — Tratamento dos casos de falha do OAuth `[P2]` `[M]`

**Área:** Backend
**Descrição:** Cobrir explicitamente os cenários da tabela de falha do
OAuth (refresh token inválido/revogado, timeout de rede).

**Critérios de aceite:**
- [ ] Cada cenário da tabela referenciada tem um teste ou verificação
      manual associada.

**Depende de:** 5.4, 5.5
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §3.7

---

## Épico 6 — Ética e observabilidade

### 6.1 — Logging mínimo por turno `[P1]` `[P]`

**Área:** Backend
**Descrição:** Logar, por turno: se passou pelo roteador ou pela
extração; sucesso/falha de cada etapa; tempo de resposta.

**Critérios de aceite:**
- [ ] Dá pra responder, olhando o log depois da demo, "quantos turnos o
      roteador resolveu sozinho vs. quantos precisaram do LLM".

**Depende de:** 3.2
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §8

### 6.2 — Exposição de diversidade/cobertura na UI `[P2]` `[P]`

**Área:** Frontend
**Descrição:** Mostrar, opcionalmente, a métrica de diversidade de
gênero do resultado na tela (não só no log).

**Critérios de aceite:**
- [ ] Indicador visível, mesmo que discreto, quando o resultado usa
      popularidade como parte do ranking.

**Depende de:** 1.4, 4.2
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §8;
`RELATORIO.md` (análise de mercado) — princípio ético do projeto

### 6.3 — Métrica de cobertura de matching do OAuth `[P2]` `[P]`

**Área:** Dados
**Descrição:** Expor (ao menos em log) a taxa de cobertura do matching
por sessão autenticada.

**Critérios de aceite:**
- [ ] Métrica calculada e logada a cada login com histórico buscado.

**Depende de:** 5.6
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §3.5, §8

---

## Épico 7 — Testes e preparação da demo

### 7.1 — Testar os casos de uso do pipeline `[P0]` `[M]`

**Área:** QA
**Descrição:** Passar manualmente pelos 12 casos de uso já documentados.

**Critérios de aceite:**
- [ ] Cada caso de uso testado e resultado anotado (passou/não passou).

**Depende de:** 3.2, 4.1
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §6

### 7.2 — Testar edge cases sem depender de conta Spotify real `[P0]` `[M]`

**Área:** QA
**Descrição:** LLM indisponível, JSON malformado, histórico de conversa
longo, `n_resultados` absurdo, sessão inválida após restart do backend.

**Critérios de aceite:**
- [ ] Cada edge case da tabela referenciada testado, sem depender de
      OAuth.

**Depende de:** 3.2, 2.7
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §7

### 7.3 — Testar fluxo OAuth completo com conta de teste `[P1]` `[M]`

**Área:** QA
**Descrição:** Login, negação de permissão de propósito, verificação do
perfil de gosto calculado.

**Critérios de aceite:**
- [ ] Login bem-sucedido e negado testados.
- [ ] Perfil de gosto conferido manualmente contra o histórico real da
      conta de teste.

**Depende de:** 5.7
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §10

### 7.4 — Testar expiração e renovação de token `[P2]` `[P]`

**Área:** QA
**Descrição:** Forçar um token expirado (manualmente) e confirmar a
renovação automática.

**Critérios de aceite:**
- [ ] Renovação acontece sem pedir login de novo ao usuário.

**Depende de:** 5.4
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §3.3, §10

### 7.5 — Testar concorrência de conversas simultâneas `[P1]` `[P]`

**Área:** QA
**Descrição:** Duas conversas ao mesmo tempo contra o mesmo Ollama
local, confirmando que não trava o backend inteiro.

**Critérios de aceite:**
- [ ] Segunda conversa recebe resposta (mesmo que mais lenta) ou cai no
      timeout/fallback de forma limpa, sem erro 500.

**Depende de:** 0.2, 3.2
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §7, §10

### 7.6 — Ensaio geral na configuração de rede da demo `[P0]` `[P]`

**Área:** QA/Infra
**Descrição:** Rodar a demo inteira (login opcional incluso, se already
implementado) na configuração de rede escolhida (ticket 0.5), antes do
dia da apresentação.

**Critérios de aceite:**
- [ ] Ensaio completo feito com pelo menos 1 dia de antecedência da
      apresentação.

**Depende de:** 0.5, 7.1, 7.2
**Referência:** [`PIPELINE_AGENTE_PROPOSTA_B.md`](PIPELINE_AGENTE_PROPOSTA_B.md) §10
