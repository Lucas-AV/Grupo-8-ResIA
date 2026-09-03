"""Contratos entre a API e o pipeline conversacional."""

from .contracts import PipelineUnavailableError, TurnProcessor

__all__ = ["PipelineUnavailableError", "TurnProcessor"]
