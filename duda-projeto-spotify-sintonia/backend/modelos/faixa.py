"""Contratos musicais migrados do protótipo TypeScript."""

from pydantic import BaseModel, ConfigDict, Field


class AtributosAudio(BaseModel):
    """Atributos disponíveis no dataset oficial, ainda sem transformação de ML."""

    model_config = ConfigDict(extra="forbid")

    danceability: float | None = Field(default=None, ge=0, le=1)
    energy: float | None = Field(default=None, ge=0, le=1)
    loudness: float | None = None
    speechiness: float | None = Field(default=None, ge=0, le=1)
    acousticness: float | None = Field(default=None, ge=0, le=1)
    instrumentalness: float | None = Field(default=None, ge=0, le=1)
    liveness: float | None = Field(default=None, ge=0, le=1)
    valence: float | None = Field(default=None, ge=0, le=1)
    tempo: float | None = Field(default=None, ge=0)
    duration_ms: int | None = Field(default=None, ge=0)
    popularity: float | None = Field(default=None, ge=0, le=100)
    key: int | None = None
    mode: int | None = None
    time_signature: int | None = None


class Faixa(AtributosAudio):
    """Representação canônica de uma faixa no catálogo tratado."""

    track_id: str = Field(min_length=1)
    nome: str = Field(min_length=1)
    artistas: list[str] = Field(min_length=1)
    album: str | None = None
    generos: list[str] = Field(default_factory=list)
    explicita: bool | None = None
    fonte: str = Field(min_length=1)

