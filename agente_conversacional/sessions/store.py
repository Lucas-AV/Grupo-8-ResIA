"""Armazenamento de sessões de chat, persistido em SQLite (ticket KAN-8).

Antes disso era um dict Python puro — qualquer restart do processo (deploy,
crash, ou só reiniciar o servidor em dev) apagava todas as sessões, e o
frontend descartava o cache local junto (ver app.js's
carregarHistoricoInicial: sessão não reconhecida pelo backend = "conversa
nova", mesmo com histórico salvo no navegador). Guardar em disco resolve
isso sem mudar nada de quem consome `SessionStore` — a API pública é
idêntica à versão em memória.

Sem `db_path` explícito, o default é `:memory:` (mesmo comportamento efêmero
de sempre, isolado por instância) — usado pela suíte de testes e por
qualquer chamador que não precise sobreviver a um restart. `app.py` passa um
caminho de arquivo real (`SESSION_DB_PATH`, default `sessions.db`) pro
servidor de verdade."""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Callable, Iterable

from .models import Message, SessionContext, SessionMetrics, TurnResult

DEFAULT_TIMEOUT_MINUTES = 30
_DEFAULT_DB_PATH = ":memory:"


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
class _SessionRow:
    session_id: str
    last_activity: datetime
    perfil_usuario: tuple[float, ...] | None
    autenticada: bool
    faixas_ja_mostradas: set[str]
    generos_mostrados: set[str]
    soma_cobertura: float
    turnos_com_recomendacao: int


class SessionStore:
    """Sessões efêmeras (ou persistidas, com `db_path`) e seguras para uso
    concorrente no processo atual."""

    def __init__(
        self,
        timeout_minutes: int | None = None,
        clock: Callable[[], datetime] = utc_now,
        db_path: str | None = None,
    ) -> None:
        configured_timeout = timeout_minutes or timeout_minutes_from_environment()
        self._timeout = timedelta(minutes=configured_timeout)
        self._clock = clock
        self._lock = threading.RLock()
        self._db_path = db_path or _DEFAULT_DB_PATH
        # Uma unica conexao pra vida da instancia (necessario pra `:memory:`
        # funcionar — cada `sqlite3.connect(":memory:")` novo abre um banco
        # vazio e isolado). O RLock ja serializa todo acesso, entao uma
        # conexao compartilhada entre chamadas e segura aqui.
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._init_db()

    def _init_db(self) -> None:
        with self._conn:
            self._conn.execute(
                """CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    last_activity TEXT NOT NULL,
                    perfil_usuario TEXT,
                    autenticada INTEGER NOT NULL DEFAULT 0,
                    faixas_ja_mostradas TEXT NOT NULL DEFAULT '[]',
                    generos_mostrados TEXT NOT NULL DEFAULT '[]',
                    soma_cobertura REAL NOT NULL DEFAULT 0.0,
                    turnos_com_recomendacao INTEGER NOT NULL DEFAULT 0
                )"""
            )
            self._conn.execute(
                """CREATE TABLE IF NOT EXISTS session_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
                    ordem INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    conteudo TEXT NOT NULL,
                    faixas_citadas TEXT NOT NULL DEFAULT '[]',
                    timestamp TEXT NOT NULL
                )"""
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_session_messages_session_id ON session_messages(session_id)"
            )

    def create(self) -> str:
        with self._lock:
            now = self._now()
            self._purge_expired_locked(now)
            session_id = str(uuid.uuid4())
            with self._conn:
                self._conn.execute(
                    "INSERT INTO sessions (session_id, created_at, last_activity) VALUES (?, ?, ?)",
                    (session_id, now.isoformat(), now.isoformat()),
                )
            return session_id

    def get_context(self, session_id: str) -> SessionContext:
        with self._lock:
            row = self._get_active_row_locked(session_id)
            self._touch_locked(session_id, self._now())
            historico = self._fetch_messages_locked(session_id)
            return self._context_from_row(row, historico)

    def get_history(self, session_id: str) -> tuple[Message, ...]:
        with self._lock:
            self._get_active_row_locked(session_id)
            self._touch_locked(session_id, self._now())
            return self._fetch_messages_locked(session_id)

    def commit_turn(self, session_id: str, mensagem_usuario: str, result: TurnResult) -> None:
        """Grava as duas mensagens somente depois de um turno bem-sucedido."""

        with self._lock:
            row = self._get_active_row_locked(session_id)
            now = self._now()

            faixas_ja_mostradas = row.faixas_ja_mostradas | {track.track_id for track in result.faixas}
            generos_mostrados = row.generos_mostrados | {track.genero for track in result.faixas}
            soma_cobertura = row.soma_cobertura
            turnos = row.turnos_com_recomendacao
            if result.faixas:
                soma_cobertura += result.cobertura_sessao
                turnos += 1

            with self._conn:
                proxima_ordem = self._proxima_ordem_locked(session_id)
                self._conn.execute(
                    """INSERT INTO session_messages
                       (session_id, ordem, role, conteudo, faixas_citadas, timestamp)
                       VALUES (?, ?, 'usuario', ?, '[]', ?)""",
                    (session_id, proxima_ordem, mensagem_usuario, now.isoformat()),
                )
                self._conn.execute(
                    """INSERT INTO session_messages
                       (session_id, ordem, role, conteudo, faixas_citadas, timestamp)
                       VALUES (?, ?, 'agente', ?, ?, ?)""",
                    (
                        session_id,
                        proxima_ordem + 1,
                        result.mensagem,
                        json.dumps(list(result.faixas_citadas)),
                        now.isoformat(),
                    ),
                )
                self._conn.execute(
                    """UPDATE sessions SET
                        faixas_ja_mostradas = ?,
                        generos_mostrados = ?,
                        soma_cobertura = ?,
                        turnos_com_recomendacao = ?,
                        last_activity = ?
                       WHERE session_id = ?""",
                    (
                        json.dumps(sorted(faixas_ja_mostradas)),
                        json.dumps(sorted(generos_mostrados)),
                        soma_cobertura,
                        turnos,
                        now.isoformat(),
                        session_id,
                    ),
                )

    def mark_authenticated(
        self,
        session_id: str,
        perfil_usuario: Iterable[float] | None = None,
    ) -> None:
        """Ponto de integração do OAuth: promove a sessão já existente."""

        with self._lock:
            self._get_active_row_locked(session_id)
            now = self._now()
            perfil_json = json.dumps(list(perfil_usuario)) if perfil_usuario is not None else None
            with self._conn:
                self._conn.execute(
                    "UPDATE sessions SET autenticada = 1, perfil_usuario = ?, last_activity = ? WHERE session_id = ?",
                    (perfil_json, now.isoformat(), session_id),
                )

    def purge_expired(self) -> int:
        with self._lock:
            return self._purge_expired_locked(self._now())

    def count(self) -> int:
        with self._lock:
            self._purge_expired_locked(self._now())
            return self._conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]

    def _get_active_row_locked(self, session_id: str) -> _SessionRow:
        now = self._now()
        self._purge_expired_locked(now)
        cursor = self._conn.execute(
            """SELECT session_id, last_activity, perfil_usuario, autenticada,
                      faixas_ja_mostradas, generos_mostrados, soma_cobertura, turnos_com_recomendacao
               FROM sessions WHERE session_id = ?""",
            (session_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise SessionNotFound(session_id)
        return self._row_to_state(row)

    def _touch_locked(self, session_id: str, now: datetime) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE sessions SET last_activity = ? WHERE session_id = ?",
                (now.isoformat(), session_id),
            )

    def _proxima_ordem_locked(self, session_id: str) -> int:
        maximo = self._conn.execute(
            "SELECT COALESCE(MAX(ordem), -1) FROM session_messages WHERE session_id = ?",
            (session_id,),
        ).fetchone()[0]
        return maximo + 1

    def _fetch_messages_locked(self, session_id: str) -> tuple[Message, ...]:
        cursor = self._conn.execute(
            """SELECT role, conteudo, faixas_citadas, timestamp FROM session_messages
               WHERE session_id = ? ORDER BY ordem ASC""",
            (session_id,),
        )
        return tuple(
            Message(
                role=role,
                conteudo=conteudo,
                faixas_citadas=tuple(json.loads(faixas_citadas)),
                timestamp=datetime.fromisoformat(timestamp),
            )
            for role, conteudo, faixas_citadas, timestamp in cursor.fetchall()
        )

    def _purge_expired_locked(self, now: datetime) -> int:
        # <= (nao so <): o timeout original comparava `now - last_activity >= timeout`,
        # entao uma sessao exatamente no limite ja conta como expirada.
        limite = (now - self._timeout).isoformat()
        with self._conn:
            cursor = self._conn.execute("DELETE FROM sessions WHERE last_activity <= ?", (limite,))
            return cursor.rowcount if cursor.rowcount is not None and cursor.rowcount > 0 else 0

    def _row_to_state(self, row: tuple) -> _SessionRow:
        session_id, last_activity, perfil_usuario, autenticada, faixas_ja_mostradas, generos_mostrados, soma_cobertura, turnos = row
        return _SessionRow(
            session_id=session_id,
            last_activity=datetime.fromisoformat(last_activity),
            perfil_usuario=tuple(json.loads(perfil_usuario)) if perfil_usuario is not None else None,
            autenticada=bool(autenticada),
            faixas_ja_mostradas=set(json.loads(faixas_ja_mostradas)),
            generos_mostrados=set(json.loads(generos_mostrados)),
            soma_cobertura=soma_cobertura,
            turnos_com_recomendacao=turnos,
        )

    def _context_from_row(self, row: _SessionRow, historico: tuple[Message, ...]) -> SessionContext:
        coverage = row.soma_cobertura / row.turnos_com_recomendacao if row.turnos_com_recomendacao else 0.0
        return SessionContext(
            session_id=row.session_id,
            historico=historico,
            perfil_usuario=row.perfil_usuario,
            autenticada=row.autenticada,
            faixas_ja_mostradas=frozenset(row.faixas_ja_mostradas),
            metricas=SessionMetrics(
                diversidade_generos=len(row.generos_mostrados),
                cobertura_media=coverage,
                turnos_com_recomendacao=row.turnos_com_recomendacao,
            ),
        )

    def _now(self) -> datetime:
        now = self._clock()
        return now.replace(tzinfo=UTC) if now.tzinfo is None else now.astimezone(UTC)
