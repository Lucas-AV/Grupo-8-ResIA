"""Interfaces que serão implementadas pelo pipeline do Épico 2."""

from typing import Protocol

from ..sessions.models import SessionContext, TurnResult


class PipelineUnavailableError(Exception):
    """O processador não pode atender o turno neste momento."""


class TurnProcessor(Protocol):
    def process(self, mensagem: str, contexto: SessionContext) -> TurnResult:
        """Transforma uma mensagem e seu contexto em uma resposta auditável."""
