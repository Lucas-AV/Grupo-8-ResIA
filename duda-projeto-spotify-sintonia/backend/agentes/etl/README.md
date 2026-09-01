# Agente de ETL

O módulo `pipeline.py` é a fonte única de transformação do Spotify Tracks
Dataset. O notebook acadêmico chama as mesmas funções para manter consistência
entre a análise e o backend.

## Uso

```python
from backend.agentes.etl import executar_etl

resultado = executar_etl()
catalogo = resultado.dados_tratados
agregacao = resultado.agregacao_por_genero
```

O pipeline procura `dados/brutos/dataset.csv`, valida o schema, remove dados
inválidos e duplicados, consolida uma faixa por `track_id`, padroniza gêneros e
adiciona as colunas de áudio `*_norm` em escala 0–1.

Artefatos gerados:

- `dados/tratados/spotify_tracks_tratado.csv`;
- `dados/tratados/agregacao_por_genero.csv`;
- `dados/tratados/metadados_etl.json`;
- `dados/modelos/normalizador_atributos.joblib`.
