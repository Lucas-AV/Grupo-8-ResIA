"""Armazenamento em memória para sessões de chat do MVP."""

from __future__ import annotations

import os
import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Callable, Iterable

from .models import Message, SessionContext, SessionMetrics, TurnResult

DEFAULT_TIMEOUT_MINUTES = 30


class SessionNotFound(Exception):
    """A sessão não existe ou já expirou."""


def timeout_minutes_from_environment() -> int:
    """Lê o timeout sem impedir o boot quando a variável está inválida."""

    raw_value = os.environ.get("SESSION_TIMEOUT_MINUTES")
    if raw_value is None:
        return DEFAULT_TIMEOUT_MINUTES
    try:
        value = int(raw_value)
    except ValueError:
        return DEFAULT_TIMEOUT_MINUTES
    return value if value > 0 else DEFAULT_TIMEOUT_MINUTES


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass
class _SessionState:
    session_id: str
    created_at: datetime
    last_activity: datetime
    historico: list[Message] = field(default_factory=list)
    perfil_usuario: tuple[float, ...] | None = None
    autenticada: bool = False
    faixas_ja_mostradas: set[str] = field(default_factory=set)
    generos_mostrados: set[str] = field(default_factory=set)
    soma_cobertura: float = 0.0
    turnos_com_recomendacao: int = 0


class SessionStore:
    """Sessões efêmeras e seguras para uso concorrente no processo atual."""

    def __init__(
        self,
        timeout_minutes: int | None = None,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        configured_timeout = timeout_minutes or timeout_minutes_from_environment()
        self._timeout = timedelta(minutes=configured_timeout)
        self._clock = clock
        self._lock = threading.RLock()
        self._sessions: dict[str, _SessionState] = {}

    def create(self) -> str:
        with self._lock:
            now = self._now()
            self._purge_expired_locked(now)
            session_id = str(uuid.uuid4())
            self._sessions[session_id] = _SessionState(
                session_id=session_id,
                created_at=now,
                last_activity=now,
            )
            return session_id

    def get_context(self, session_id: str) -> SessionContext:
        with self._lock:
            state = self._get_active_locked(session_id)
            state.last_activity = self._now()
            return self._context_from_state(state)

    def get_history(self, session_id: str) -> tuple[Message, ...]:
        with self._lock:
            state = self._get_active_locked(session_id)
            state.last_activity = self._now()
            return tuple(state.historico)

    def commit_turn(self, session_id: str, mensagem_usuario: str, result: TurnResult) -> None:
        """Grava as duas mensagens somente depois de um turno bem-sucedido."""

        with self._lock:
            state = self._get_active_locked(session_id)
            now = self._now()
            state.historico.extend(
                (
                    Message("usuario", mensagem_usuario, (), now),
                    Message("agente", result.mensagem, tuple(result.faixas_citadas), now),
                )
            )
            state.faixas_ja_mostradas.update(track.track_id for track in result.faixas)
            state.generos_mostrados.update(track.genero for track in result.faixas)
            if result.faixas:
                state.soma_cobertura += result.cobertura_sessao
                state.turnos_com_recomendacao += 1
            state.last_activity = now

    def mark_authenticated(
        self,
        session_id: str,
        perfil_usuario: Iterable[float] | None = None,
    ) -> None:
        """Ponto de integração do OAuth: promove a sessão já existente."""

        with self._lock:
            state = self._get_active_locked(session_id)
            state.autenticada = True
            state.perfil_usuario = tuple(perfil_usuario) if perfil_usuario is not None else None
            state.last_activity = self._now()

    def purge_expired(self) -> int:
        with self._lock:
            return self._purge_expired_locked(self._now())

    def count(self) -> int:
        with self._lock:
            self._purge_expired_locked(self._now())
            return len(self._sessions)

    def _get_active_locked(self, session_id: str) -> _SessionState:
        now = self._now()
        self._purge_expired_locked(now)
        state = self._sessions.get(session_id)
        if state is None:
            raise SessionNotFound(session_id)
        return state

    def _purge_expired_locked(self, now: datetime) -> int:
        expired_ids = [
            session_id
            for session_id, state in self._sessions.items()
            if now - state.last_activity >= self._timeout
        ]
        for session_id in expired_ids:
            del self._sessions[session_id]
        return len(expired_ids)

    def _context_from_state(self, state: _SessionState) -> SessionContext:
        coverage = (
            state.soma_cobertura / state.turnos_com_recomendacao
            if state.turnos_com_recomendacao
            else 0.0
        )
        return SessionContext(
            session_id=state.session_id,
            historico=tuple(state.historico),
            perfil_usuario=state.perfil_usuario,
            autenticada=state.autenticada,
            faixas_ja_mostradas=frozenset(state.faixas_ja_mostradas),
            metricas=SessionMetrics(
                diversidade_generos=len(state.generos_mostrados),
                cobertura_media=coverage,
                turnos_com_recomendacao=state.turnos_com_recomendacao,
            ),
        )

    def _now(self) -> datetime:
        now = self._clock()
        return now.replace(tzinfo=UTC) if now.tzinfo is None else now.astimezone(UTC)
