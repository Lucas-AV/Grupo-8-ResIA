# Organização dos dados

- `brutos/`: cópia imutável do dataset oficial.
- `tratados/`: saída validada do ETL.
- `amostras/`: dados pequenos e anônimos para testes.
- `modelos/`: scaler, clustering e metadados de treinamento.
- `sistema/`: banco SQLite local da demonstração, nunca versionado.

Cada artefato deverá ter origem, data, schema, quantidade de registros e versão do pipeline.

