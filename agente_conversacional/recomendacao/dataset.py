import functools
from pathlib import Path

import pandas as pd

# As mesmas 9 features de audio continuas usadas na analise de correlacao
# do projeto (scripts/plot_correlations.py) — key/mode/time_signature ficam
# de fora por serem discretas/categoricas, tratadas como filtros, nao como
# dimensoes de similaridade.
FEATURES_AUDIO = [
    "danceability",
    "energy",
    "loudness",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
]

FEATURES_AUDIO_NORM = [f"{coluna}_norm" for coluna in FEATURES_AUDIO]

_CAMINHO_PADRAO = Path(__file__).resolve().parents[2] / "data" / "processed" / "dataset.csv"


@functools.lru_cache(maxsize=1)
def carregar_dataset(caminho=None):
    """Carrega o dataset.csv e devolve o DataFrame pronto pro motor de
    recomendacao. So le do disco na primeira chamada por `caminho` — o
    resultado fica cacheado (`buscar_recomendacoes` chama isso a cada busca
    sem custo de I/O repetido)."""
    caminho_resolvido = Path(caminho) if caminho is not None else _CAMINHO_PADRAO
    df = pd.read_csv(caminho_resolvido, index_col=0)

    df["track_id_duplicado"] = df["track_id"].duplicated(keep=False)

    # Colunas originais preservadas (filtros/buckets em 1.3 usam a escala
    # crua); as colunas `_norm` sao a entrada do calculo de similaridade.
    df[FEATURES_AUDIO_NORM] = _padronizar(df[FEATURES_AUDIO])

    return df


def _padronizar(colunas):
    media = colunas.mean()
    desvio = colunas.std(ddof=0).replace(0, 1)  # evita divisao por zero em coluna constante
    return (colunas - media) / desvio
