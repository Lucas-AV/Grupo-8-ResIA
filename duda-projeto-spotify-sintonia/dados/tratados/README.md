# Dados tratados

Esta pasta recebe os artefatos ignorados pelo Git produzidos pelo ETL:

- `spotify_tracks_tratado.csv`: uma linha canônica por `track_id`, sem nulos
  remanescentes e com atributos normalizados `*_norm`;
- `agregacao_por_genero.csv`: contagem e médias por gênero para o agente de
  descoberta;
- `metadados_etl.json`: proveniência, hash do CSV e decisões de tratamento.

Execute o notebook acadêmico ou `backend.agentes.etl.executar_etl()` para
regerar os arquivos a partir de `dados/brutos/dataset.csv`.
