"""Conversão estrutural de uma linha Kaggle para o contrato interno."""

from collections.abc import Mapping
from typing import Any

from backend.modelos.faixa import Faixa

from .normalizacao import normalizar_genero, valores_unicos_normalizados


def _texto(valor: Any) -> str:
    return valor.strip() if isinstance(valor, str) else ""


def _numero(valor: Any) -> float | int | None:
    return valor if isinstance(valor, (int, float)) and not isinstance(valor, bool) else None


def faixa_do_kaggle(linha: Mapping[str, Any]) -> Faixa | None:
    """Porta o adapter antigo; validações completas permanecem TODO(Fase 1)."""

    track_id = _texto(linha.get("track_id"))
    nome = _texto(linha.get("track_name"))
    if not track_id or not nome:
        return None

    artistas_brutos = _texto(linha.get("artists")).replace(",", ";").split(";")
    artistas = valores_unicos_normalizados([item for item in artistas_brutos if item.strip()])
    genero = _texto(linha.get("track_genre"))

    return Faixa(
        track_id=track_id,
        nome=nome,
        artistas=artistas,
        album=_texto(linha.get("album_name")) or None,
        generos=[normalizar_genero(genero)] if genero else [],
        explicita=linha.get("explicit") if isinstance(linha.get("explicit"), bool) else None,
        popularity=_numero(linha.get("popularity")),
        danceability=_numero(linha.get("danceability")),
        energy=_numero(linha.get("energy")),
        loudness=_numero(linha.get("loudness")),
        speechiness=_numero(linha.get("speechiness")),
        acousticness=_numero(linha.get("acousticness")),
        instrumentalness=_numero(linha.get("instrumentalness")),
        liveness=_numero(linha.get("liveness")),
        valence=_numero(linha.get("valence")),
        tempo=_numero(linha.get("tempo")),
        duration_ms=_numero(linha.get("duration_ms")),
        key=_numero(linha.get("key")),
        mode=_numero(linha.get("mode")),
        time_signature=_numero(linha.get("time_signature")),
        fonte="kaggle-spotify-tracks",
    )

