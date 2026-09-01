"""Associação de top tracks ao catálogo Kaggle local, sem chamar audio features."""

from __future__ import annotations

from math import isnan
from pathlib import Path
from threading import RLock
from typing import Any

import pandas as pd

from .modelos import AtributosSpotify

COLUNAS_ATRIBUTOS = [
    "danceability",
    "energy",
    "valence",
    "tempo",
    "acousticness",
    "instrumentalness",
    "speechiness",
    "liveness",
    "loudness",
]
COLUNAS_CATALOGO = [*COLUNAS_ATRIBUTOS, *[f"{coluna}_norm" for coluna in COLUNAS_ATRIBUTOS]]


class CatalogoAtributos:
    """Cache de leitura do CSV tratado, invalidado ao mudar o arquivo."""

    def __init__(self, caminho: str | Path = "dados/tratados/spotify_tracks_tratado.csv") -> None:
        self.caminho = Path(caminho)
        self._indice: dict[str, dict[str, Any]] = {}
        self._modificado_em: float | None = None
        self._lock = RLock()

    def obter(self, track_id: str) -> AtributosSpotify | None:
        self._atualizar_se_necessario()
        dados = self._indice.get(track_id)
        return AtributosSpotify(**dados) if dados else None

    def _atualizar_se_necessario(self) -> None:
        if not self.caminho.exists():
            return
        modificado_em = self.caminho.stat().st_mtime
        with self._lock:
            if self._modificado_em == modificado_em:
                return
            dados = pd.read_csv(self.caminho, usecols=["track_id", *COLUNAS_CATALOGO])
            indice: dict[str, dict[str, Any]] = {}
            for linha in dados.to_dict(orient="records"):
                track_id = str(linha.pop("track_id"))
                indice[track_id] = {
                    coluna: float(valor)
                    for coluna, valor in linha.items()
                    if valor is not None and not (isinstance(valor, float) and isnan(valor))
                }
            self._indice = indice
            self._modificado_em = modificado_em
