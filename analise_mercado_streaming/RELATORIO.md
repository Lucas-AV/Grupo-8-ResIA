# Sinal do Streaming — Relatório de Mercado e Pitch de Investimento

Grupo 8 · Residência em IA (UnB / LabLivre / Instituto Eldorado) · Nano-Challenge CBL
Agosto de 2026

> Versão navegável com os 7 gráficos embutidos: gerada como artefato Claude a
> partir deste mesmo conteúdo. Este arquivo é a versão de referência versionada
> no repositório — os números e a proveniência de cada um vivem aqui.

## Legenda de proveniência

Nem todo número abaixo foi divulgado oficialmente nesse formato. Cada um está
marcado:

- **[OFICIAL]** — divulgado diretamente pela fonte.
- **[CALCULADO]** — derivado por nós a partir de números oficiais (fórmula
  explicitada).
- **[ESTIMATIVA]** — estimativa de terceiros, não confirmada pela empresa.

Isso segue o mesmo princípio ético do projeto: um número sem proveniência
marcada é tão arriscado quanto uma recomendação sem explicação.

## 01 — Metodologia

Dados curados manualmente em agosto de 2026 (não é raspagem automática) de
quatro famílias de fontes: relatórios trimestrais SEC 6-K / press releases da
Spotify Technology S.A.; o *IFPI Global Music Report 2026*, via cobertura da
Music Business Worldwide e Billboard; o relatório anual da Pró-Música Brasil
(divulgado junto ao IFPI em 18/03/2026); e o modelo de participação de mercado
da MIDiA Research, via reportagem da Chartlex.

Todo o processamento estatístico e os 7 gráficos deste relatório rodam em um
script **Julia** isolado (`analise_mercado.jl`, pacotes `CSV.jl`,
`DataFrames.jl` e `Plots.jl`/GR) — decisão de arquitetura deliberada: o
pipeline de dados do agente de recomendação é em Python, mas a análise de
mercado do pitch usa stack própria, sem se misturar ao notebook principal.

Reproduzir:

```bash
julia setup.jl              # cria o ambiente isolado e instala CSV/DataFrames/Plots
julia analise_mercado.jl    # gera os 7 gráficos .png e os números deste relatório
```

## 02 — Spotify: crescimento trimestral

Gráficos: `output_spotify_usuarios.png`, `output_spotify_receita.png`,
`output_spotify_margem.png`

- MAU cresceu **15,1%** (675M → 777M) e assinantes Premium **14,1%**
  (263M → 300M) entre 2024-Q4 e 2026-Q2. **[OFICIAL]**
- Receita trimestral subiu de €4.242M para €4.777M no período. **[OFICIAL]**
- Margem operacional de 2026-Q1 (15,8%) é **[CALCULADO]**:
  `operating_income ÷ total_revenue`, já que a Spotify não divulgou esse
  percentual arredondado.
- 2026-Q2 não tem margem operacional calculada: a Spotify só detalhou o lucro
  operacional em USD nesse trimestre, sem abrir a receita em EUR necessária —
  preferimos deixar em branco a empilhar uma conversão de câmbio sobre uma
  estimativa.

## 03 — Mercado global de música gravada (IFPI)

Gráfico: `output_mercado_global.png`

- Mercado global bateu **US$ 31,7bi em 2025**, com streaming = **69,6%** do
  total (US$ 22,06bi). **[OFICIAL]**
- Crescimento de +6,4% a/a em 2025 (vs. +4,7% em 2024). **[OFICIAL]**
- Valores de 2024 para assinatura paga, físico e direitos de execução são
  **[CALCULADO]**: partimos da taxa de crescimento a/a divulgada pelo IFPI
  (ex.: streaming pago cresceu 8,8% em 2025) e dividimos o valor de 2025 por
  1,088 para estimar 2024.
- O piso histórico de US$ 13,1bi em 2014 é uma âncora retrospectiva citada na
  cobertura do relatório de 2026, não um número do relatório de 2014 em si —
  mostra que a indústria mais que dobrou de valor desde o fundo do mercado
  físico.
- Fontes diferentes (IFPI, MIDiA, Spotify) definem "mercado" de formas
  distintas — receita de gravadora, gasto do consumidor e assinantes pagos não
  são a mesma régua. Não somamos entre tabelas.

## 04 — Assinantes pagos globais

Gráfico: `output_assinantes_globais.png`

- 509M (2021) → 837M (2025) assinantes pagos globais. **[OFICIAL]**
- *Net adds* anuais desaceleram: 94M (2022) → 73M (2025) — o mercado ainda
  cresce, mas já passou do ponto mais íngreme da curva de adoção. Pesa a favor
  de crescer por **engajamento e retenção** (o que um agente conversacional
  ataca diretamente) em vez de só aquisição de novos assinantes.

## 05 — Brasil vs. mundo

Gráfico: `output_brasil_vs_global.png`

- Brasil cresceu **14,1%** em 2025 contra **6,4%** do mercado global —
  **2,2× mais rápido**. **[OFICIAL]** (Pró-Música Brasil)
- Subiu do **#10 (2023)** para **#8 (2025)** no ranking global IFPI.
  **[OFICIAL]**
- `streaming_share_pct` de 86% em 2025 é **[CALCULADO]** a partir dos dois
  valores em R$ divulgados separadamente (R$ 3,4bi de R$ 3,96bi).
- Não encontramos receita total em R$ para 2023 e 2024 nas fontes consultadas
  — só a posição no ranking. Lacuna de dado registrada, não preenchida por
  extrapolação.

## 06 — Concorrência entre plataformas

Gráfico: `output_market_share.png`

| Plataforma | Participação | Assinantes (M) | Proveniência |
|---|---|---|---|
| Spotify | 31,4% | 300 | **[OFICIAL]** |
| Tencent Music | 13,8% | 127,4 | **[OFICIAL]** (China) |
| Apple Music | 12,6% | — | **[ESTIMATIVA]** de terceiros — não divulga desde 2023 |
| YouTube Music | 12,4% | 125 | **[OFICIAL]**, agregado com YouTube Premium |
| Outros | 29,8% | — | **[CALCULADO]** — resíduo (100% menos as 4 acima) |

- Apple e Amazon não divulgam assinantes publicamente — o número de Apple
  Music é estimativa de analistas, não dado oficial.
- "Outros" agrega Amazon Music, Deezer, Tidal e demais — não é uma plataforma
  única.
- Índice de concentração **HHI ≈ 2377** → mercado moderadamente concentrado.
  Como "Outros" está agregado, o HHI real (com cada plataforma menor
  separada) tende a ser um pouco mais baixo do que essa aproximação.
- Mesmo princípio aplicado aqui — não tratar um número agregado/estimado como
  fato monolítico — guia o motor de recomendação do produto: sempre que
  `popularity` for usado como sinal, reportamos junto uma métrica de
  diversidade/cobertura das recomendações.

## 07 — O pitch: por que investir agora

**Problema.** Catálogos com centenas de milhares de faixas, mas a experiência
de descoberta continua sendo ranking e playlist genérica — sem diálogo, sem
explicação do porquê da recomendação.

**Timing de mercado.** Mercado global de streaming ainda em expansão (+6,4%
a/a) — e o Brasil subiu 3 posições no ranking IFPI em 2 anos, crescendo 14,1%
em 2025: momentum superior à média global, no mercado de origem do time.

**Concorrência.** HHI ≈ 2377 é concentração moderada, não monopólio: Spotify
lidera com 31,4%, mas quase 70% do mercado está dividido ou em plataformas
que não abrem seu motor de recomendação a auditoria.

**A solução.** LLM conduz a conversa via tool-calling sobre uma função
determinística de recomendação por conteúdo (k-NN / similaridade de
cosseno). O LLM nunca inventa faixa — só narra um resultado real. Fallback
determinístico por palavra-chave garante a demo mesmo se a API cair.

**Por que não é risco técnico alto.** O motor content-based não depende de
matriz usuário-item que não existe no dataset — trabalha só com metadado e
features de áudio que já estão nas 114 mil faixas reais.

**Vantagem ética como diferencial.** Compromisso de medir diversidade/
cobertura sempre que popularidade for sinal de recomendação — resposta direta
ao mesmo problema de "filter bubble" que já pesa contra incumbentes.

**O que o investimento habilita (ask).**

- Dados reais de interação de usuário, para fechar o gap de collaborative
  filtering (o dataset atual não tem matriz usuário-item).
- Login via Spotify OAuth, casando histórico real do usuário com as features
  já presentes no dataset local — a API de audio-features do Spotify foi
  descontinuada para apps novos desde nov/2024, então não dá pra pedir isso à
  API diretamente.
- Evolução para um modelo híbrido (conteúdo + colaborativo).

**Riscos assumidos, não escondidos.**

- ~24.259 `track_id` duplicados no dataset (mesma faixa em vários gêneros) —
  tratamento documentado, não ignorado.
- Dados de mercado deste relatório são curadoria manual de agosto/2026, não
  um feed automático: servem para validar direção estratégica, não como
  cotação de preço.

## 08 — Fontes e limitações gerais

- **Spotify** — SEC Form 6-K e press releases/shareholder letters, Q4 2024 a
  Q2 2026.
- **Mercado global** — IFPI Global Music Report 2026 (dados de 2025), via
  Music Business Worldwide e Billboard.
- **Brasil** — relatório anual da Pró-Música Brasil, divulgado junto ao IFPI
  em 18/03/2026.
- **Participação de mercado** — modelo da MIDiA Research para fim de 2025,
  via reportagem da Chartlex (agosto/2026).

Séries temporais têm poucos pontos (dados anuais para mercado global/Brasil,
trimestrais só para Spotify) — qualquer tendência extraída deve ser lida como
ilustrativa, não preditiva. Ver `data/FONTES.md` para o detalhamento completo
por planilha.
