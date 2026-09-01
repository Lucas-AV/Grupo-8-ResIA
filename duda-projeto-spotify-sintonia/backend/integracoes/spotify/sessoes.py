"""Sessões OAuth efêmeras: tokens permanecem apenas na memória do backend."""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from threading import RLock
from typing import Any


@dataclass
class SessaoSpotify:
    estado: str
    criada_em: datetime
    token_info: dict[str, Any] | None = None
    expira_em: datetime = field(default_factory=lambda: datetime.now(UTC) + timedelta(hours=2))


class ArmazenamentoSessoesSpotify:
    """Armazenamento local para demonstração; reiniciar o servidor exige login."""

    def __init__(self) -> None:
        self._sessoes: dict[str, SessaoSpotify] = {}
        self._lock = RLock()

    def criar(self) -> tuple[str, str]:
        identificador = secrets.token_urlsafe(32)
        estado = secrets.token_urlsafe(32)
        with self._lock:
            self._limpar_expiradas()
            self._sessoes[identificador] = SessaoSpotify(estado=estado, criada_em=datetime.now(UTC))
        return identificador, estado

    def obter(self, identificador: str | None) -> SessaoSpotify | None:
        if not identificador:
            return None
        with self._lock:
            self._limpar_expiradas()
            return self._sessoes.get(identificador)

    def salvar_token(self, identificador: str, token_info: dict[str, Any]) -> None:
        with self._lock:
            sessao = self.obter(identificador)
            if sessao is None:
                raise KeyError("Sessão Spotify inexistente.")
            sessao.token_info = token_info
            sessao.expira_em = datetime.now(UTC) + timedelta(hours=2)

    def remover(self, identificador: str | None) -> None:
        if identificador:
            with self._lock:
                self._sessoes.pop(identificador, None)

    def _limpar_expiradas(self) -> None:
        agora = datetime.now(UTC)
        for identificador in [chave for chave, sessao in self._sessoes.items() if sessao.expira_em <= agora]:
            self._sessoes.pop(identificador, None)
