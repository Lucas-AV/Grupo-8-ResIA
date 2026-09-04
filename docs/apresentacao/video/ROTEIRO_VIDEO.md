# Roteiro do vídeo — 5 minutos

O vídeo apresenta o MelodIA com linguagem direta, demonstra o fluxo principal
e fecha com a arquitetura responsável. A narração abaixo foi dimensionada para
cerca de cinco minutos em ritmo natural, com pausas curtas entre pessoas.

## Mapa de cenas

| Cena | Tempo | Duração | Responsável | Conteúdo na tela | Corte |
| ---: | --- | ---: | --- | --- | --- |
| 1 | 00:00–00:20 | 20 s | Pessoa 1 | Câmera e capa do MelodIA | Entrada suave para o slide 1 |
| 2 | 00:20–00:55 | 35 s | Pessoa 2 | Problema e exemplos de pedidos | Aproximação no texto principal |
| 3 | 00:55–01:35 | 40 s | Pessoa 3 | Gráfico Brasil versus mundo | Corte seco para o gráfico |
| 4 | 01:35–02:20 | 45 s | Pessoa 4 | Jornada da conversa | Elementos entram na ordem do fluxo |
| 5 | 02:20–03:00 | 40 s | Pessoa 5 | Separação entre LLM e busca | Destaque em “faixas reais” |
| 6 | 03:00–03:45 | 45 s | Pessoa 6 | Captura da demo | Cursor visível e sem música |
| 7 | 03:45–04:30 | 45 s | Pessoa 5 | Dados, diversidade e notebook | Alternar números e heatmap |
| 8 | 04:30–05:00 | 30 s | Pessoa 1 | Equipe e próximos passos | Volta para câmera e encerra |
|  | **Total** | **300 s** |  |  |  |

## Texto narrado

### Cena 1 — Pessoa 1 — 00:00 a 00:20

“Encontrar uma música parece simples até o momento em que o pedido foge de uma
playlist pronta. O MelodIA é um agente de recomendação musical criado pelo
Grupo 8 da Residência em Inteligência Artificial. Ele transforma uma conversa
curta em uma lista de músicas reais, com critérios que podem ser explicados.”

### Cena 2 — Pessoa 2 — 00:20 a 00:55

“Hoje, catálogos oferecem milhares de faixas, mas a descoberta ainda depende
muito de rankings, buscas por nome e listas genéricas. Uma pessoa pode querer
pagode animado, rock mais calmo para trabalhar ou músicas alegres sem conteúdo
explícito. Esses pedidos misturam intenção, contexto e preferência. Nossa
proposta permite escrevê-los como falamos no dia a dia, sem aprender filtros
técnicos nem percorrer várias telas.”

### Cena 3 — Pessoa 3 — 00:55 a 01:35

“O projeto nasce em um mercado que continua relevante. Em 2025, o mercado
global de música gravada cresceu 6,4 por cento. O Brasil cresceu 14,1 por cento
no mesmo período, mais que o dobro da média mundial, e avançou do décimo para o
oitavo lugar no ranking global entre 2023 e 2025. Esses dados não garantem o
sucesso de um produto, mas mostram espaço para experiências que melhorem a
descoberta e o vínculo com o catálogo.”

### Cena 4 — Pessoa 4 — 01:35 a 02:20

“O uso começa com uma mensagem. O sistema identifica gênero, energia, clima,
artista de referência e outras preferências. Depois consulta um conjunto local
de músicas, compara características de áudio e devolve uma lista estruturada.
O frontend transforma essa lista em cards fáceis de explorar. O login com
Spotify é opcional. Quando autorizado, ele pode acrescentar sinais do histórico
de escuta. Sem login, o fluxo principal continua disponível. Essa escolha
reduz barreiras e também protege a demonstração contra falhas externas.”

### Cena 5 — Pessoa 5 — 02:20 a 03:00

“O modelo de linguagem tem um papel limitado. Ele ajuda a interpretar pedidos
livres e a escrever uma resposta natural. A seleção das músicas acontece em um
motor determinístico feito em Python. Antes de exibir a resposta, uma auditoria
confere se cada identificador citado realmente veio da busca. Se o modelo ficar
indisponível, o sistema usa um texto simples para apresentar as mesmas faixas.
Se o pedido não puder ser entendido, pede esclarecimento em vez de inventar um
resultado.”

### Cena 6 — Pessoa 6 — 03:00 a 03:45

“Na demonstração, escrevemos ‘quero um pagode animado’. Esse pedido conhecido
passa pelo roteador de regras, por isso funciona mesmo sem o modelo de linguagem
e sem login. O motor consulta o catálogo e a tela recebe texto, faixas e métricas
em campos separados. Aqui aparecem os cards com nome, artista, álbum e gênero.
A resposta também informa a diversidade do resultado e quantas faixas ainda
não tinham aparecido na conversa.”

### Cena 7 — Pessoa 5 — 03:45 a 04:30

“O conjunto processado reúne 128.830 registros, equivalentes a 97.534 faixas
únicas em 118 gêneros. Há 31.296 registros repetidos porque uma música pode
pertencer a mais de um gênero. A análise preserva essa informação, enquanto a
recomendação evita repetir a mesma faixa. O notebook mostra também relações
entre características de áudio. Energia e volume percebido caminham juntos,
com correlação de 0,775. Energia e caráter acústico seguem direções opostas,
com menos 0,742. Nenhuma característica isolada explica a popularidade.”

### Cena 8 — Pessoa 1 — 04:30 a 05:00

“O MelodIA reúne uma interface simples, uma busca verificável e uso controlado
de inteligência artificial. O próximo passo é aprender com interações reais e
evoluir a personalização sem perder transparência. O repositório documenta os
dados, a arquitetura, os testes e as limitações conhecidas. Essa base permite
avançar com clareza sobre o que o sistema faz hoje e sobre o que ainda precisa
ser validado com pessoas.”

## Clipe reserva da demo — 45 segundos

1. **0–5 s:** mostrar a tela vazia e o texto “Fluxo sem login”.
2. **5–12 s:** digitar “quero um pagode animado”.
3. **12–27 s:** mostrar a resposta e percorrer dois cards.
4. **27–37 s:** destacar diversidade e cobertura.
5. **37–45 s:** mostrar “Busca controlada, faixas reais, fallback disponível”.

Gravar sem áudio de músicas. A fala pode ser narrada ao vivo se o clipe for
usado durante a banca.
