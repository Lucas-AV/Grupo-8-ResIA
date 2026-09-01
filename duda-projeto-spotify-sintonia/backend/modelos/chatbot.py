"""Contratos de intenção, recomendação, confiança e revisão humana."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from .faixa import Faixa


class Intencao(StrEnum):
    DESCOBERTA = "descoberta"
    RECOMENDACAO = "recomendacao"
    EXPLICACAO = "explicacao"
    CONVERSA_LIVRE = "conversa_livre"
    DESCONHECIDA = "desconhecida"


class StatusResposta(StrEnum):
    RESPONDER = "responder"
    REVISAO_HUMANA = "revisao_humana"


class Interpretacao(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intencao: Intencao
    entidades: dict[str, list[str] | str | int | float | bool | None] = Field(default_factory=dict)
    confianca: float = Field(ge=0, le=1)


class Recomendacao(BaseModel):
    model_config = ConfigDict(extra="forbid")

    faixa: Faixa
    score_afinidade: float = Field(ge=0, le=1)
    score_confianca: float = Field(ge=0, le=1)
    explicacao: str
    sinais_utilizados: list[str] = Field(default_factory=list)


class DecisaoConfianca(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confianca: float = Field(ge=0, le=1)
    limiar: float = Field(default=0.90, ge=0, le=1)
    status: StatusResposta
    motivos: list[str] = Field(default_factory=list)


class RespostaChatbot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    texto: str
    intencao: Intencao
    decisao: DecisaoConfianca
    recomendacoes: list[Recomendacao] = Field(default_factory=list)


class CasoRevisao(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    mensagem_usuario: str
    proposta_json: str
    confianca: float = Field(ge=0, le=1)
    motivo: str
    status: str = "aberto"
    criado_em: datetime
    resolvido_em: datetime | None = None

