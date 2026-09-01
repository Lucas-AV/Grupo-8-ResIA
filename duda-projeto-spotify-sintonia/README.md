# Spotify Insights & Recommender Chatbot

Projeto acadêmico da Universidade de Brasília (UnB), desenvolvido na disciplina **Sistemas de Machine Learning** com metodologia CBL.

O objetivo é reduzir a sensação de recomendação musical em “caixa-preta”. O sistema deverá agrupar faixas por atributos de áudio, compreender o perfil musical do usuário, recomendar músicas novas, explicar cada escolha e encaminhar respostas inseguras para revisão humana.

> Estado atual: estrutura inicial e migração seletiva do protótipo anterior. O pipeline de ML, a recomendação e o chatbot ainda não estão implementados.

## Regra obrigatória de confiança

Toda saída do chatbot deverá possuir um score de confiança. Se a confiança for menor que **90%**, o sistema não responde automaticamente: ele cria um caso para revisão humana.

## Como os módulos se conectam

```text
Usuário → Frontend → Orquestrador
                       ├── Coleta Spotify
                       ├── ETL
                       ├── Agente de clustering → Núcleo ML
                       ├── Conversacional
                       └── Confiança/HITL
                                ├── confiança ≥ 90% → resposta
                                └── confiança < 90% → revisão humana
```

## Agentes do sistema

1. **Orquestrador** — identifica a intenção (`descoberta`, `recomendacao`, `explicacao` ou `conversa_livre`) e coordena os demais módulos.
2. **Coleta Spotify** — cuida do OAuth e obtém, com consentimento, artistas, faixas e histórico disponível.
3. **ETL** — valida, limpa, deduplica e transforma o dataset e os sinais do usuário.
4. **Clustering** — chama o núcleo matemático, interpreta os clusters e classifica o usuário.
5. **Conversacional** — transforma resultados estruturados em conversa natural PT-BR, sem inventar dados.
6. **Confiança e HITL** — calcula confiança, bloqueia saídas abaixo de 90% e mantém a fila de revisão humana.

O diretório `backend/agentes/clustering/` representa o agente coordenador. O algoritmo de ML ficará isolado em `backend/nucleo_ml/clustering_faixas/`.

## Estrutura principal

- `dados/`: entradas brutas, dados tratados, amostras e artefatos de modelos.
- `notebooks/`: entregável acadêmico com EDA, ETL, clustering, hipóteses e plots.
- `backend/`: agentes, integração Spotify, contratos, persistência e núcleo de ML.
- `frontend/`: interface Next.js migrada sem a lógica quebrada do protótipo.
- `testes/`: testes unitários, de integração, dados e frontend.
- `documentacao/`: arquitetura, decisões, migração da Fase 0 e referências.
- `resultados/`: plots e métricas produzidos pelo notebook/pipeline.
- `apresentacao/`: material da apresentação final da disciplina.

## Preparação do ambiente Python

Recomendação: **Python 3.13**.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Copie `.env.example` para `.env` e preencha somente o arquivo local. Nunca versione credenciais.

## Frontend

```powershell
cd frontend
npm ci
npm run dev
```

Nesta fase o frontend é apenas uma casca visual estática. Botões que dependerão do backend estão identificados como indisponíveis até as próximas fases.

## Dados oficiais

Dataset: [Spotify Tracks Dataset — Kaggle](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset).

O CSV bruto deve ser colocado em `dados/brutos/` e não será versionado. Consulte `dados/brutos/README.md` antes de utilizá-lo.

## Migração do protótipo anterior

Foram preservados apenas contratos, normalizações, conceitos de segurança, OAuth PKCE e elementos visuais classificados como reaproveitáveis. A conversa por regex, recomendação por busca textual, clustering coletivo e dependências específicas do D1/Sites não foram migrados para o código ativo.

O inventário completo está em `documentacao/migracao_fase0.md` e as próximas implementações estão em `TODO.md`.
