"""Schemas HTTP do KAN-8."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class SessionResponse(BaseModel):
    session_id: str


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    mensagem: str

    @field_validator("mensagem")
    @classmethod
    def mensagem_nao_pode_ser_vazia(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("mensagem não pode ser vazia")
        return value


class TrackItem(BaseModel):
    track_id: str
    nome: str
    artista: str
    album: str
    genero: str


class ChatResponse(BaseModel):
    session_id: str
    mensagem: str
    faixas: list[TrackItem] = Field(default_factory=list)
    diversidade_generos: int
    cobertura_sessao: float
    consulta_efetiva: dict[str, Any] = Field(default_factory=dict)


class HistoryMessage(BaseModel):
    role: Literal["usuario", "agente", "sistema"]
    conteudo: str
    faixas_citadas: list[str] = Field(default_factory=list)
    timestamp: datetime


class ChatHistoryResponse(BaseModel):
    session_id: str
    historico: list[HistoryMessage] = Field(default_factory=list)


class RecomendarResponse(BaseModel):
    """Resposta do GET /recomendar (ticket 12.3) — mesmo shape de `faixas` do
    ChatResponse, mas sem `session_id`/`mensagem`: esse endpoint chama
    `buscar_recomendacoes` direto, sem sessao nem LLM envolvidos."""

    faixas: list[TrackItem] = Field(default_factory=list)
    diversidade_generos: int
    cobertura_sessao: float
    consulta_efetiva: dict[str, Any] = Field(default_factory=dict)
