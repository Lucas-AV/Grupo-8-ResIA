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

## Sumário

- [Grupo 8 — ResIA: Agente de Recomendação de Músicas](#grupo-8--resia-agente-de-recomendação-de-músicas)
  - [Sumário](#sumário)
  - [Equipe](#equipe)
  - [Sugestões de nome do projeto](#sugestões-de-nome-do-projeto)
  - [Base de dados](#base-de-dados)
  - [Estrutura do repositório](#estrutura-do-repositório)
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

`dataset.csv` contém ~114 mil faixas distribuídas em 114 gêneros, com colunas:

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
dataset.csv                    # dataset bruto (Kaggle)
group_occurrences.py           # agrupa dataset.csv por coluna e por track_genre
occurrences_by_column.csv      # contagem de valores por coluna (formato longo)
occurrences_by_genre.csv       # contagem de faixas + médias por gênero
chart_style.py                 # estilo/cores compartilhados entre os scripts de gráfico
plot_genre_charts.py           # gera genre_popularity.png e genre_energy_dance.png
plot_genre_mode.py             # gera genre_mode.png (proporção de escala maior/menor)
plot_popularity_occurrences.py # gera popularity_occurrences.png (popularidade x nº de faixas do artista)
profile_dataset.py             # gera dataset_profile.json e distribuições de faixas por artista/álbum
plot_correlations.py           # gera correlation_heatmap.png e correlations_top_pairs.csv
site/                          # build do dashboard (build_site.py, templates/, static/)
tests/                         # testes automatizados (pytest)
conftest.py                    # config do pytest (path do projeto)
requirements.txt               # dependências Python
.github/workflows/pages.yml    # workflow de deploy do site no GitHub Pages
```

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
| [pandas](https://pandas.pydata.org/) | Biblioteca de manipulação e análise de dados tabulares (DataFrames) | Ler o `dataset.csv`, agrupar por coluna/gênero e calcular médias/contagens (`group_occurrences.py`, `site/build_site.py`) |
| [matplotlib](https://matplotlib.org/) | Biblioteca de geração de gráficos estáticos | Gerar os PNGs das análises (`plot_genre_charts.py`, `plot_genre_mode.py`, `plot_popularity_occurrences.py`) |
| [adjustText](https://github.com/Phlya/adjustText) | Reposiciona rótulos de texto em gráficos matplotlib para evitar sobreposição | Afastar os rótulos de gênero que se sobrepunham no scatter de energia × dançabilidade (`genre_energy_dance.png`) |
| [Jinja2](https://jinja.palletsprojects.com/) | Motor de templates para gerar texto/HTML a partir de dados | Renderizar as páginas HTML do site (`site/build_site.py` + `site/templates/`) |
| [pytest](https://docs.pytest.org/) | Framework de testes automatizados | Rodar os testes do repositório (`tests/`) |

## Como reproduzir

```bash
pip install -r requirements.txt
python group_occurrences.py           # gera os CSVs agregados
python plot_genre_charts.py           # gera genre_popularity.png e genre_energy_dance.png
python plot_genre_mode.py             # gera genre_mode.png
python plot_popularity_occurrences.py # gera popularity_occurrences.png
python profile_dataset.py             # gera dataset_profile.json e distribuicoes por artista/album
python plot_correlations.py           # gera correlation_heatmap.png e correlations_top_pairs.csv
python site/build_site.py             # gera o site em site/dist/ (abrir site/dist/index.html)
```

Testes: `pytest`

## Roadmap

- [x] Análise exploratória por gênero (popularidade, energia, dançabilidade, escala)
- [x] Site GitHub Pages com dashboard interativo das análises publicado em https://lucas-av.github.io/Grupo-8-ResIA/
- [ ] Modelagem do agente de recomendação (conteúdo/colaborativo/híbrido)
- [ ] Avaliação com dataset complementar de interação/avaliação de usuários

## Licença

[MIT](LICENSE) — Copyright (c) 2026 Lucas Alves Vilela
