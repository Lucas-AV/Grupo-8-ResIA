# Roteiro técnico — 8 minutos

Esta apresentação explica a arquitetura implementada e o papel limitado do
LLM. Os detalhes aparecem sempre ligados a uma decisão de produto: controle,
continuidade da demo, privacidade ou facilidade de manutenção.

## Tempos

| Slide | Tema | Tempo |
| ---: | --- | ---: |
| 1 | Escopo técnico | 20 s |
| 2 | Componentes do sistema | 45 s |
| 3 | Fluxo completo de uma mensagem | 65 s |
| 4 | Regras e LLM | 50 s |
| 5 | Contrato estruturado e validação | 45 s |
| 6 | Similaridade e perfil | 50 s |
| 7 | Segurança, fallback e métricas | 50 s |
| 8 | Spotify, PKCE e privacidade | 40 s |
| 9 | Notebook ao vivo | 90 s |
| 10 | Testes, limites e evolução | 25 s |
| **Total** |  | **480 s** |

## Falas e demonstrações

### 1. Escopo técnico — 20 segundos

“A apresentação técnica mostra como uma mensagem vira uma recomendação e em
quais pontos o modelo de linguagem participa. A arquitetura mantém a seleção
de músicas fora do LLM para facilitar testes e auditoria.”

### 2. Componentes do sistema — 45 segundos

“O frontend conversa apenas com o backend FastAPI. O backend organiza sessões,
executa o pipeline e protege credenciais. O conjunto processado fica local e é
carregado pelo motor de recomendação. Ollama é o backend padrão do LLM e existe
uma alternativa hospedada configurável. O Spotify entra de forma opcional para
autenticação, histórico e busca complementar.”

### 3. Fluxo completo de uma mensagem — 65 segundos

“O turno começa no endpoint de chat. Primeiro carregamos o contexto da sessão.
Um roteador por regras resolve pedidos simples. Quando ele não resolve, o LLM
extrai uma consulta estruturada. A validação remove valores inválidos. A busca
por similaridade escolhe as faixas. Depois, o LLM pode transformar a lista em
uma resposta natural. Uma auditoria compara os identificadores citados com o
resultado real antes de devolver texto e cards ao frontend.”

### 4. Regras e LLM — 50 segundos

“As regras atendem saudações, pedidos conhecidos e situações fora do escopo.
Elas são rápidas e previsíveis. O LLM entra em duas tarefas: compreender frases
mais livres e escrever uma resposta natural. Ele não recebe liberdade para
buscar ou escolher músicas. Essa separação permite trocar o modelo e manter o
mesmo motor de recomendação.”

### 5. Contrato estruturado e validação — 45 segundos

“A extração retorna sete campos: gênero, energia, valência, dançabilidade,
artista de referência, exclusão de conteúdo explícito e quantidade. O backend
limita a quantidade entre um e trinta e descarta valores que não existem no
conjunto. Se o LLM enviar texto em volta do JSON, o extrator tenta recuperar o
primeiro objeto válido.”

### 6. Similaridade e perfil — 50 segundos

“O conjunto atual tem 128.830 registros e 97.534 faixas únicas. Nove
características de áudio são padronizadas e comparadas por similaridade de
cosseno. Um artista de referência gera um perfil médio. Quando existe histórico
Spotify compatível, o pedido recebe peso de setenta por cento e o perfil da
pessoa recebe trinta por cento. Sem sinal suficiente, a busca usa popularidade
e pode completar o resultado pela busca do Spotify.”

### 7. Segurança, fallback e métricas — 50 segundos

“A geração só recebe as faixas já escolhidas. A auditoria remove
identificadores que não estejam no resultado e registra divergências. Se o LLM
falhar, um texto determinístico apresenta a mesma lista. Se nem o roteador nem
a extração entenderem o pedido, o sistema pede esclarecimento sem fazer uma
busca vazia. Os logs registram o trajeto, o tempo e o uso de fallback. A
resposta também informa diversidade e cobertura.”

### 8. Spotify, PKCE e privacidade — 40 segundos

“O login usa Authorization Code com PKCE e validação de state. Os tokens ficam
no backend, criptografados, e nunca aparecem no frontend ou nos logs. O
histórico de escuta serve para calcular um perfil em memória. Se a API estiver
indisponível ou limitar uma chamada, a sessão continua anônima e o restante do
produto permanece utilizável.”

### 9. Notebook ao vivo — 90 segundos

Deixar o notebook aberto e executar tudo antes da apresentação. Durante a
fala, reexecutar apenas:

1. **Perfil geral do dataset:** célula de código da seção 2. Mostrar 128.830
   registros, 97.534 IDs únicos, 31.296 repetições e 118 gêneros.
2. **Correlações:** célula de código da seção 10. Destacar energia e volume
   percebido com correlação 0,775; energia e caráter acústico com -0,742.

“Esses resultados orientam a escolha das características e também deixam
claros os limites: nenhuma variável de áudio explica popularidade sozinha.”

Se o kernel falhar, usar a imagem de correlação já incorporada ao slide.

### 10. Testes, limites e evolução — 25 segundos

“O projeto possui testes para sessões, pipeline, fallback, auditoria, OAuth e
recomendação. O notebook também executa do início ao fim. Os limites atuais são
a dependência de dados agregados e as restrições da API Spotify. A evolução
esperada combina feedback real com o mecanismo atual sem entregar o controle
da busca ao LLM.”

## Preparação técnica

- Executar `python scripts/validate_notebook_demo.py`.
- Executar `python scripts/run_notebook_demo.py`.
- Abrir o notebook e usar `Restart Kernel and Run All Cells`.
- Abrir o agente em outra janela e fazer um pedido de teste.
- Manter as imagens `images/correlation_heatmap.png` e
  `images/genre_energy_dance.png` disponíveis.
- Desativar notificações e fechar qualquer tela que possa exibir credenciais.

