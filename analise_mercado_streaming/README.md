# Análise do Mercado de Streaming de Música (Julia)

Análise de visão geral combinando: mercado global (IFPI), mercado brasileiro (Pró-Música Brasil) e desempenho financeiro trimestral do Spotify, para o pitch de mercado do nano-challenge.

## Estrutura

```
analise_mercado_streaming/
├── analise_mercado.jl          # script principal
├── README.md                   # este arquivo
└── data/
    ├── spotify_quarterly.csv
    ├── global_market_revenue.csv
    ├── global_paid_subscribers.csv
    ├── brazil_market.csv
    ├── platform_market_share.csv
    └── FONTES.md                # fontes e limitações de cada dado — leia antes de citar números no relatório/pitch
```

## Como ambientar (fazer uma vez só)

Para um guia completo e específico pra **Fedora 43** (instalação do Julia via juliaup, VS Code + extensão Julia, ambiente isolado do projeto, troubleshooting), veja **`GUIA_AMBIENTE_FEDORA.md`** nesta mesma pasta.

Resumo rápido:

```bash
bash install_julia_fedora.sh   # instala o Julia
julia setup.jl                 # cria o ambiente isolado do projeto e instala CSV/DataFrames/Plots
```

## Como rodar a análise

Pelo terminal, na pasta `analise_mercado_streaming/`:

```bash
julia analise_mercado.jl
```

O script já ativa sozinho o ambiente isolado criado pelo `setup.jl` (não precisa repetir `Pkg.add`).

## O que o script gera

- Prints no console com os principais números (crescimento de MAU/assinantes da Spotify, Brasil vs. mundo, índice de concentração de mercado HHI).
- 6 gráficos `.png` salvos na mesma pasta:
  - `output_spotify_usuarios.png` — MAU e assinantes Premium por trimestre
  - `output_spotify_receita.png` — receita total por trimestre
  - `output_spotify_margem.png` — margem operacional por trimestre
  - `output_mercado_global.png` — receita global de música gravada, total vs. streaming
  - `output_assinantes_globais.png` — crescimento de assinantes pagos no mundo
  - `output_brasil_vs_global.png` — comparação de crescimento Brasil vs. mundo
  - `output_market_share.png` — participação de mercado entre plataformas

## Antes de usar os números no relatório/pitch

Leia `data/FONTES.md` — alguns valores foram **calculados por nós** a partir de taxas de crescimento divulgadas (não são números oficiais diretos), e isso está marcado explicitamente lá. Também há uma nota importante sobre a Apple e a Amazon não divulgarem assinantes publicamente (os números delas em `platform_market_share.csv` são estimativas de terceiros, não oficiais).
