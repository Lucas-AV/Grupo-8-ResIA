# Fontes e Notas Metodológicas

Dados coletados por curadoria manual de resultados de busca em agosto de 2026 — não é raspagem automática. Reflete o estado das informações públicas disponíveis até essa data.

## Spotify (`spotify_quarterly.csv`)

- **Fonte:** relatórios trimestrais de resultados da Spotify Technology S.A. (SEC Form 6-K e press releases/shareholder letters), cobrindo Q4 2024 a Q2 2026.
- `2026-Q1` operating_margin_pct foi **calculado por nós** (operating_income ÷ total_revenue) — não é um número divulgado nesse formato arredondado pela Spotify.
- Células vazias = dado não encontrado nas fontes consultadas para aquele trimestre (ex: a Spotify não detalhou publicamente a margem bruta/operacional em EUR do Q2 2026 no material consultado — só uma cifra de lucro operacional em USD, que não convertemos para não empilhar estimativas).

## Mercado global (`global_market_revenue.csv`, `global_paid_subscribers.csv`)

- **Fonte:** IFPI *Global Music Report 2026* (dados de 2025), via cobertura da Music Business Worldwide e Billboard.
- Os valores de 2024 para `paid_subscription_usd_bn`, `physical_revenue_usd_bn` e `performance_rights_usd_bn` foram **calculados por nós** a partir das taxas de crescimento YoY divulgadas pela IFPI (ex: streaming pago cresceu 8,8% em 2025 → dividimos o valor de 2025 por 1,088 para estimar 2024). Não são números publicados diretamente pela IFPI nesse recorte.
- O valor de 2014 (US$ 13,1 bi) é citado como o "ponto mais baixo" histórico da indústria, mencionado retrospectivamente na cobertura do relatório de 2026 — não vem do relatório de 2014 em si. Serve só como âncora histórica (indústria mais que dobrou de valor desde então).

## Brasil (`brazil_market.csv`)

- **Fonte:** relatório anual da Pró-Música Brasil, divulgado simultaneamente ao IFPI Global Music Report 2026 (18 de março de 2026).
- `streaming_share_pct` de 2025 foi **calculado por nós** (receita de streaming ÷ receita total), a partir dos dois valores em R$ divulgados separadamente pela Pró-Música.
- Não encontramos os valores de receita total em R$ para 2023 e 2024 nas fontes consultadas — só a posição no ranking global da IFPI para esses anos (10º em 2023, 9º em 2024, 8º em 2025).

## Participação de mercado entre plataformas (`platform_market_share.csv`)

- **Fonte:** modelo de participação de mercado da MIDiA Research para o fim de 2025, citado em reportagem da Chartlex (atualizada em agosto de 2026).
- **Importante:** Apple e Amazon não divulgam número de assinantes publicamente — os valores para essas plataformas nas fontes de mercado são **estimativas de terceiros** (analistas), não dados oficiais. Isso está marcado na coluna `disclosure_type`.
- A categoria "Outros" é um resíduo **calculado por nós** (100% menos a soma das 4 plataformas listadas) e agrega Amazon Music, Deezer, Tidal e demais plataformas menores — não é uma única plataforma.

## Limitações gerais

- Fontes diferentes (IFPI, MIDiA Research, Spotify) podem usar definições diferentes de "mercado" (receita de gravadoras/wholesale vs. gasto do consumidor vs. assinantes pagos). Não comparar/somar entre tabelas sem checar a metodologia de cada uma.
- Séries temporais têm poucos pontos (dados anuais para o mercado global/Brasil, trimestrais só para a Spotify) — qualquer regressão/tendência extraída deve ser tratada como ilustrativa, não preditiva.
