# Grupo 8 — ResIA: Agente de Recomendação de Músicas

[![Licença: MIT](https://img.shields.io/badge/Licença-MIT-yellow.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](requirements.txt)

Projeto da disciplina ResIA (Grupo 8): um agente de recomendação de músicas e
playlists construído a partir de análise de dados do Spotify. O repositório
hoje concentra a etapa de análise exploratória de dados (EDA) que fundamenta o
agente — entendimento de gêneros, popularidade e características de áudio das
faixas — e evolui para as etapas de modelagem e recomendação.

> **About (EN):** ResIA (Grupo 8) course project — a music/playlist
> recommendation agent built from exploratory analysis of a Spotify tracks
> dataset (genre, popularity, and audio features). Currently in the EDA
> stage; recommendation modeling is next.

**Quadro do Miro:** [Link do projeto](https://miro.com/app/board/uXjVHttBzWA=/)
**Quadro do JIRA:** Link do Quadro

## Sumário

- [Grupo 8 — ResIA: Agente de Recomendação de Músicas](#grupo-8--resia-agente-de-recomendação-de-músicas)
  - [Sumário](#sumário)
  - [Equipe](#equipe)
  - [Sugestões de nome do projeto](#sugestões-de-nome-do-projeto)
  - [Base de dados](#base-de-dados)
  - [Estrutura do repositório](#estrutura-do-repositório)
  - [Arquitetura do agente conversacional (Proposta B)](#arquitetura-do-agente-conversacional-proposta-b)
  - [Análises disponíveis](#análises-disponíveis)
  - [Bibliotecas](#bibliotecas)
  - [Como reproduzir](#como-reproduzir)
  - [Roadmap](#roadmap)
  - [Licença](#licença)

## Equipe

<table>
<tr>
<td align="center">
<a href="https://github.com/Lucas-AV"><img src="https://github.com/Lucas-AV.png" width="100" style="border-radius:50%" alt="Lucas Alves Vilela"></a>
<br><b>Lucas Alves Vilela</b>
<br><a href="https://github.com/Lucas-AV"><img src="https://img.shields.io/badge/GitHub-Lucas--AV-181717?logo=github&logoColor=white" alt="GitHub Lucas-AV"></a>
</td>
<td align="center">
<a href="https://github.com/dayarierref"><img src="https://github.com/dayarierref.png" width="100" style="border-radius:50%" alt="Dayane Ferreira"></a>
<br><b>Dayane Ferreira</b>
<br><a href="https://github.com/dayarierref"><img src="https://img.shields.io/badge/GitHub-dayarierref-181717?logo=github&logoColor=white" alt="GitHub dayarierref"></a>
</td>
<td align="center">
<a href="https://github.com/dudsstar16"><img src="https://github.com/dudsstar16.png" width="100" style="border-radius:50%" alt="Eduarda Reis"></a>
<br><b>Eduarda Reis</b>
<br><a href="https://github.com/dudsstar16"><img src="https://img.shields.io/badge/GitHub-dudsstar16-181717?logo=github&logoColor=white" alt="GitHub dudsstar16"></a>
</td>
<td align="center">
<a href="https://github.com/Ruan-Carvalho"><img src="https://github.com/Ruan-Carvalho.png" width="100" style="border-radius:50%" alt="Ruan Sobreira Carvalho"></a>
<br><b>Ruan Sobreira Carvalho</b>
<br><a href="https://github.com/Ruan-Carvalho"><img src="https://img.shields.io/badge/GitHub-Ruan--Carvalho-181717?logo=github&logoColor=white" alt="GitHub Ruan-Carvalho"></a>
</td>
<td align="center">
<a href="https://github.com/femathrl0"><img src="https://github.com/femathrl0.png" width="100" style="border-radius:50%" alt="femathrl0"></a>
<br><b>femathrl0</b>
<br><a href="https://github.com/femathrl0"><img src="https://img.shields.io/badge/GitHub-femathrl0-181717?logo=github&logoColor=white" alt="GitHub femathrl0"></a>
</td>
<td align="center">
<a href="https://github.com/rebecavitoriasalazar-cpu"><img src="https://github.com/rebecavitoriasalazar-cpu.png" width="100" style="border-radius:50%" alt="Rebeca Vitoria Salazar"></a>
<br><b>Rebeca Vitoria Salazar</b>
<br><a href="https://github.com/rebecavitoriasalazar-cpu"><img src="https://img.shields.io/badge/GitHub-rebecavitoriasalazar--cpu-181717?logo=github&logoColor=white" alt="GitHub rebecavitoriasalazar-cpu"></a>
</td>
</tr>
</table>

## Sugestões de nome do projeto

Candidatos para renomear o repositório (estilo: termo de música/áudio +
sufixo tech como Sense/IA):

- AudioSense
- MelodIA
- TuneSense
- RitmIA
- GrooveIA
- HarmonIA
- MoodSense

## Base de dados

Dataset: [Spotify Tracks Dataset](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset) (Kaggle).

`data/processed/dataset.csv` contém uma base ampliada de faixas e gêneros, gerada a partir das
fontes documentadas em `docs/data_enrichment/`.

- Identificação: `track_id`, `artists`, `album_name`, `track_name`, `track_genre`
- Popularidade: `popularity`
- Características de áudio: `danceability`, `energy`, `loudness`, `speechiness`,
  `acousticness`, `instrumentalness`, `liveness`, `valence`, `tempo`,
  `duration_ms`, `key`, `mode`, `time_signature`, `explicit`

> Utilizar outros datasets para lidar com limitações: "Avaliação dos usuários"
> (o dataset atual não traz histórico de escuta/feedback por usuário, apenas
> metadados e popularidade agregada da faixa).

## Estrutura do repositório

```
analise_exploratoria.ipynb     # notebook que concentra a EDA (mesma logica dos scripts abaixo, saida inline)
data/                           # fontes e artefatos do pipeline
  raw/                          # CSVs originais baixados das fontes
  processed/                    # fontes normalizadas e dataset.csv consolidado
  analytics/                    # CSVs/JSON derivados para análises e site
  hygiene/                      # validações, proveniência e rejeições
images/                         # PNGs gerados pelos scripts de análise
scripts/                        # scripts Python de análise
  chart_style.py                 # estilo/cores compartilhados entre os scripts de gráfico
  group_occurrences.py           # agrupa dataset.csv por coluna e por track_genre
  plot_genre_charts.py           # gera genre_popularity.png e genre_energy_dance.png
  plot_genre_mode.py             # gera genre_mode.png (proporção de escala maior/menor)
  plot_popularity_occurrences.py # gera popularity_occurrences.png (popularidade x nº de faixas do artista)
  profile_dataset.py             # gera dataset_profile.json e distribuições de faixas por artista/álbum
  plot_correlations.py           # gera correlation_heatmap.png e correlations_top_pairs.csv
site/                          # build do dashboard (build_site.py, templates/, static/)
tests/                         # testes automatizados (pytest)
  conftest.py                  # config do pytest (path do projeto)
requirements.txt               # dependências Python
.github/workflows/pages.yml    # workflow de deploy do site no GitHub Pages
analise_mercado_streaming/     # análise de mercado do pitch, em Julia (stack separada, ver abaixo)
agente_conversacional/         # backend + frontend do agente (Proposta B) — Épicos 0,1,3,4,5,8,12 (ver seção abaixo)
docs/PIPELINE_AGENTE_PROPOSTA_B.md  # especificação técnica completa do pipeline conversacional
docs/BACKLOG_JIRA_PROPOSTA_B.md     # backlog em tickets, 1 seção por épico do Jira
```

## Análise de mercado (Julia)

A pasta [`analise_mercado_streaming/`](analise_mercado_streaming/) contém a
análise do mercado de streaming de música (Spotify, IFPI, Pró-Música Brasil,
MIDiA Research) que fundamenta o pitch de investimento do projeto. É uma
stack separada e deliberada: enquanto o resto do repositório é Python, essa
análise roda em **Julia** (`CSV.jl`, `DataFrames.jl`, `Plots.jl`), isolada em
seu próprio ambiente (`Project.toml`/`Manifest.toml`).

- Relatório completo, com a proveniência de cada número (oficial, calculado
  por nós, ou estimativa de terceiros) e a estrutura do pitch de investimento:
  [`analise_mercado_streaming/RELATORIO.md`](analise_mercado_streaming/RELATORIO.md)
- Notas de fonte e limitações por planilha:
  [`analise_mercado_streaming/data/FONTES.md`](analise_mercado_streaming/data/FONTES.md)
- Versão no site publicado: [Mercado de Streaming](https://lucas-av.github.io/Grupo-8-ResIA/mercado.html)
- Como reproduzir: ver [`analise_mercado_streaming/README.md`](analise_mercado_streaming/README.md)
  (resumo: `julia setup.jl && julia analise_mercado.jl`)

## Arquitetura do agente conversacional (Proposta B)

O time decidiu a arquitetura do agente conversacional que vai consumir o
`dataset.csv`: um pipeline em etapas (roteador determinístico → extração
estruturada via LLM → busca determinística → geração guiada), com
integração completa a Spotify OAuth para personalizar recomendações a
partir do histórico do usuário. Dois documentos de referência cobrem essa
arquitetura ponta a ponta:

- [`docs/PIPELINE_AGENTE_PROPOSTA_B.md`](docs/PIPELINE_AGENTE_PROPOSTA_B.md)
  — especificação completa: ciclo de vida do agente, fluxo Spotify OAuth
  (PKCE), contratos de dados entre componentes, pipeline de um turno de
  conversa passo a passo, casos de uso, edge cases e plano de testes.
- [`docs/BACKLOG_JIRA_PROPOSTA_B.md`](docs/BACKLOG_JIRA_PROPOSTA_B.md) —
  o mesmo escopo reorganizado em épicos e tickets prontos para o Kanban
  do Jira, com prioridade, tamanho, dependências e referência à seção
  técnica de cada item.

## Análises disponíveis

- **`genre_popularity.png`** — popularidade média por gênero, em barras
  ranqueadas. Gênero mais popular: *chill* (53,7 de popularidade média).
- **`genre_energy_dance.png`** — dispersão energia × dançabilidade, um ponto
  por gênero. Mais energético: *death-metal* (0,93); menos energético:
  *classical* (0,19); mais dançável: *chicago-house* (0,77).
- **`genre_mode.png`** — proporção de faixas em escala maior (mode 1) vs.
  menor (mode 0) por gênero. Maior predominância de escala maior: *country*
  (89%); maior predominância de escala menor: *deep-house* (54%).
- **`popularity_occurrences.png`** — relação entre popularidade média e
  quantidade de faixas do artista na base (proxy de volume de catálogo).
- **`dataset_profile.json` / `artist_track_distribution.png` /
  `album_track_distribution.png`** — visão geral do dataset: contagem de
  faixas, artistas, álbuns e gêneros, faixas duplicadas entre gêneros, e
  distribuição de faixas por artista/álbum.
- **`correlation_heatmap.png`** — correlação de Pearson entre popularidade,
  duração e as 9 features de áudio contínuas.

## Bibliotecas

| Biblioteca | O que é | Para que serve neste projeto |
|---|---|---|
| [pandas](https://pandas.pydata.org/) | Biblioteca de manipulação e análise de dados tabulares (DataFrames) | Ler o `data/processed/dataset.csv`, agrupar por coluna/gênero e calcular médias/contagens (`scripts/group_occurrences.py`, `site/build_site.py`); carregar e normalizar o dataset pro motor de recomendação (`agente_conversacional/recomendacao/dataset.py`) |
| [matplotlib](https://matplotlib.org/) | Biblioteca de geração de gráficos estáticos | Gerar os PNGs das análises (`scripts/plot_genre_charts.py`, `scripts/plot_genre_mode.py`, `scripts/plot_popularity_occurrences.py`) |
| [adjustText](https://github.com/Phlya/adjustText) | Reposiciona rótulos de texto em gráficos matplotlib para evitar sobreposição | Afastar os rótulos de gênero que se sobrepunham no scatter de energia × dançabilidade (`genre_energy_dance.png`) |
| [Jinja2](https://jinja.palletsprojects.com/) | Motor de templates para gerar texto/HTML a partir de dados | Renderizar as páginas HTML do site (`site/build_site.py` + `site/templates/`) |
| [pytest](https://docs.pytest.org/) | Framework de testes automatizados | Rodar os testes do repositório (`tests/`) |
| [JupyterLab](https://jupyterlab.readthedocs.io/) | Ambiente de notebooks interativos | Rodar `analise_exploratoria.ipynb`, o notebook que concentra a EDA |

## Como reproduzir

```bash
pip install -r requirements.txt
python scripts/group_occurrences.py           # gera os CSVs agregados em data/
python scripts/plot_genre_charts.py           # gera images/genre_popularity.png e images/genre_energy_dance.png
python scripts/plot_genre_mode.py             # gera images/genre_mode.png
python scripts/plot_popularity_occurrences.py # gera images/popularity_occurrences.png
python scripts/profile_dataset.py             # gera arquivos de perfil em data/analytics/
python scripts/plot_correlations.py           # gera correlation_heatmap.png e pares em data/analytics/
python site/build_site.py                     # gera o site em site/dist/ (abrir site/dist/index.html)
jupyter lab analise_exploratoria.ipynb        # abre o notebook de EDA (mesma logica, saida inline)
```

Testes: `pytest`

## Demonstração do notebook

O notebook de EDA está pronto para uma demonstração guiada, célula a célula. Veja as opções online e os comandos de verificação em [`docs/NOTEBOOK_DEMO.md`](docs/NOTEBOOK_DEMO.md). Para abrir e executar pelo navegador sem preparar ambiente local, use o [Binder](https://mybinder.org/v2/gh/Lucas-AV/Grupo-8-ResIA/HEAD?labpath=analise_exploratoria.ipynb).

## Roadmap

- [x] Análise exploratória por gênero (popularidade, energia, dançabilidade, escala)
- [x] Site GitHub Pages com dashboard interativo das análises publicado em https://lucas-av.github.io/Grupo-8-ResIA/
- [x] Análise de mercado (Julia) e pitch de investimento
- [x] Arquitetura do agente conversacional definida (Proposta B) — ver
      [`docs/PIPELINE_AGENTE_PROPOSTA_B.md`](docs/PIPELINE_AGENTE_PROPOSTA_B.md)
      e backlog em [`docs/BACKLOG_JIRA_PROPOSTA_B.md`](docs/BACKLOG_JIRA_PROPOSTA_B.md)
- [x] Épico 0 — Infraestrutura de LLM implementada e testada (Ollama +
      backend Claude alternativo, health-check, logística de rede da demo) —
      ver [`agente_conversacional/`](agente_conversacional/)
- [x] Épico 1 — Motor de recomendação (`recomendacao/`): dataset normalizado,
      índice de similaridade, `buscar_recomendacoes` completa, diversidade/
      cobertura, fallback via Spotify Search API quando o catálogo local não
      cobre o pedido
- [x] Épico 2 — Pipeline conversacional (roteador determinístico → extração
      via LLM → busca → geração/auditoria), integrado ao `POST /chat` com
      fallback seguro e testes ponta a ponta
- [x] Épico 3 — Backend/API de sessões (`POST /session`, `POST /chat`,
      `GET /chat/historico`) — ver
      [`agente_conversacional/docs/KAN-8_BACKEND_API.md`](agente_conversacional/docs/KAN-8_BACKEND_API.md)
- [x] Épico 4 — Frontend do chat (tela, cards de faixa, indicador de
      processando, login com Spotify) — falta só o fluxo de logout (4.5)
- [x] Épico 5 — Integração Spotify OAuth completa: login PKCE, tokens
      criptografados, matching de histórico com o dataset local, perfil de
      gosto (centróide) injetado na recomendação
- [x] Épico 8 — Infra de projeto: CORS, tratamento de erro global, CI
      (pytest em todo push/PR), rate limiter pronto (falta só ligar no
      `/chat`)
- [x] Épico 12 — Funcionalidades extras: criar playlist real no Spotify a
      partir da recomendação, endpoint de recomendação sem depender do LLM,
      dark mode, landing page do projeto
- [ ] Modelagem do agente de recomendação (conteúdo/colaborativo/híbrido)
- [ ] Avaliação com dataset complementar de interação/avaliação de usuários
      (pesquisa de hábitos musicais roteirizada em `docs/pesquisa/`, ainda
      não publicada/coletada)

## Licença

[MIT](LICENSE) — Copyright (c) 2026 Lucas Alves Vilela
