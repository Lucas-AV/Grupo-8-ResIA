# Notebook acadêmico

`spotify_eda_etl_clustering_hipoteses.ipynb` é o entregável de dados da
disciplina. Ele contém o relatório de qualidade, decisões de ETL, GQ1, GQ6
parcial, gráficos, agregação por gênero e seções preservadas para clustering.

Com o ambiente virtual ativado, abra-o pelo Jupyter usando o kernel
`Python (spotify-insights-unb)`. O CSV original deve permanecer em
`dados/brutos/dataset.csv`.

Para reproduzir integralmente sem interface gráfica:

```powershell
.\.venv\Scripts\jupyter-nbconvert.exe --to notebook --execute --inplace `
  --ExecutePreprocessor.kernel_name=spotify-insights-unb `
  notebooks\spotify_eda_etl_clustering_hipoteses.ipynb
```
