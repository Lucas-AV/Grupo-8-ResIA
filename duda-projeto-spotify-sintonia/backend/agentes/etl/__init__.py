"""ETL reutilizável do catálogo Spotify."""

from .pipeline import (
    ALIASES_GENERO,
    ATRIBUTOS_AUDIO,
    ResultadoETL,
    agregar_por_genero,
    carregar_dataset,
    diagnosticar_dados,
    executar_etl,
    localizar_csv_bruto,
    normalizar_atributos_audio,
    padronizar_nome_genero,
    tratar_dataset,
)

__all__ = [
    "ALIASES_GENERO",
    "ATRIBUTOS_AUDIO",
    "ResultadoETL",
    "agregar_por_genero",
    "carregar_dataset",
    "diagnosticar_dados",
    "executar_etl",
    "localizar_csv_bruto",
    "normalizar_atributos_audio",
    "padronizar_nome_genero",
    "tratar_dataset",
]
