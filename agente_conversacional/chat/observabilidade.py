"""Eventos mínimos e seguros para acompanhar cada turno do chat.

Os eventos não registram mensagem, identificador de sessão, tokens ou dados de
conta. Isso permite entender o caminho do turno sem expor a conversa.
"""

import logging

logger = logging.getLogger("agente.chat.turno")


def registrar_turno(*, rota, extracao, busca, geracao, auditoria, resultado, duracao_ms):
    """Registra as etapas e a duração de um turno em formato estável."""
    logger.info(
        "turno rota=%s extracao=%s busca=%s geracao=%s auditoria=%s resultado=%s duracao_ms=%d",
        rota, extracao, busca, geracao, auditoria, resultado, round(duracao_ms),
    )
