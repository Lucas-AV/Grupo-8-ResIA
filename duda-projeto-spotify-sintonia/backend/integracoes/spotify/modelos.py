"""Contratos sem segredos para a coleta Spotify."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PeriodoSpotify = Literal["short_term", "medium_term", "long_term"]
OrigemAtributos = Literal["catalogo_kaggle", "demo", "indisponivel"]
FonteColeta = Literal["spotify_api", "demo"]


class AtributosSpotify(BaseModel):
    """Atributos compatíveis com o catálogo, nunca obtidos de endpoint obsoleto."""

    model_config = ConfigDict(extra="forbid")

    danceability: float | None = Field(default=None, ge=0, le=1)
    energy: float | None = Field(default=None, ge=0, le=1)
    valence: float | None = Field(default=None, ge=0, le=1)
    tempo: float | None = Field(default=None, ge=0)
    acousticness: float | None = Field(default=None, ge=0, le=1)
    instrumentalness: float | None = Field(default=None, ge=0, le=1)
    speechiness: float | None = Field(default=None, ge=0, le=1)
    liveness: float | None = Field(default=None, ge=0, le=1)
    loudness: float | None = None
    danceability_norm: float | None = Field(default=None, ge=0, le=1)
    energy_norm: float | None = Field(default=None, ge=0, le=1)
    valence_norm: float | None = Field(default=None, ge=0, le=1)
    tempo_norm: float | None = Field(default=None, ge=0, le=1)
    acousticness_norm: float | None = Field(default=None, ge=0, le=1)
    instrumentalness_norm: float | None = Field(default=None, ge=0, le=1)
    speechiness_norm: float | None = Field(default=None, ge=0, le=1)
    liveness_norm: float | None = Field(default=None, ge=0, le=1)
    loudness_norm: float | None = Field(default=None, ge=0, le=1)


class FaixaSpotify(BaseModel):
    model_config = ConfigDict(extra="forbid")

    posicao: int = Field(ge=1)
    track_id: str
    nome: str
    artistas: list[str]
    album: str | None = None
    explicita: bool | None = None
    uri: str | None = None
    url_spotify: str | None = None
    atributos_audio: AtributosSpotify | None = None
    origem_atributos: OrigemAtributos


class ArtistaSpotify(BaseModel):
    model_config = ConfigDict(extra="forbid")

    posicao: int = Field(ge=1)
    artista_id: str
    nome: str
    generos: list[str] = Field(default_factory=list)
    url_spotify: str | None = None


class PerfilSpotify(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id_pseudonimo: str
    nome_exibicao: str | None = None
    imagem_url: str | None = None


class ColetaSpotify(BaseModel):
    """Resposta auditável para o agente de coleta e para a API."""

    model_config = ConfigDict(extra="forbid")

    fonte: FonteColeta
    periodo: PeriodoSpotify
    coletado_em: datetime
    perfil: PerfilSpotify
    top_faixas: list[FaixaSpotify] = Field(default_factory=list)
    top_artistas: list[ArtistaSpotify] = Field(default_factory=list)
    avisos: list[str] = Field(default_factory=list)
