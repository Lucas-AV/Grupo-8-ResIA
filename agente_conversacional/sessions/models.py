"""Contratos de domínio independentes de FastAPI para uma conversa."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Mapping


MessageRole = Literal["usuario", "agente", "sistema"]


@dataclass(frozen=True)
class Track:
    """Uma faixa que veio do motor de recomendação determinístico."""

    track_id: str
    nome: str
    artista: str
    album: str
    genero: str


@dataclass(frozen=True)
class Message:
    role: MessageRole
    conteudo: str
    faixas_citadas: tuple[str, ...]
    timestamp: datetime


@dataclass(frozen=True)
class SessionMetrics:
    diversidade_generos: int
    cobertura_media: float
    turnos_com_recomendacao: int


@dataclass(frozen=True)
class SessionContext:
    """Visão imutável da sessão entregue ao pipeline de conversa."""

    session_id: str
    historico: tuple[Message, ...]
    perfil_usuario: tuple[float, ...] | None
    autenticada: bool
    faixas_ja_mostradas: frozenset[str]
    metricas: SessionMetrics


@dataclass(frozen=True)
class TurnResult:
    """Resultado que o futuro pipeline (Épico 2) entrega para a API."""

    mensagem: str
    faixas: tuple[Track, ...]
    diversidade_generos: int
    cobertura_sessao: float
    consulta_efetiva: Mapping[str, object]
    faixas_citadas: tuple[str, ...] = ()
