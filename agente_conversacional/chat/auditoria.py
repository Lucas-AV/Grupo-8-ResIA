"""Ticket 2.6 — auditoria mecânica de `faixas_citadas`: checagem
automática (não só instrução de prompt) de que toda faixa citada no
texto gerado pelo LLM (ticket 2.5) corresponde a um `track_id` que veio
de verdade do resultado de `buscar_recomendacoes` daquele turno. Cobre o
edge case de manipulação de prompt (seção 7): mesmo que o LLM ceda a uma
instrução maliciosa, essa camada mecânica filtra qualquer citação que
não bate com o resultado real e loga a divergência."""

import logging
from dataclasses import dataclass

logger = logging.getLogger("agente.chat.auditoria")


@dataclass(frozen=True)
class AuditoriaResultado:
    citadas_validas: tuple
    divergentes: tuple


def auditar_citacoes(citadas, faixas_resultado):
    """Compara `citadas` (o que o texto gerado alega ter citado) com os
    `track_id`s realmente presentes em `faixas_resultado`. Devolve as
    citações válidas (na ordem original, sem duplicatas) e as
    divergentes — a divergência é sempre logada (visível), mas não
    bloqueia a resposta (ainda MVP, ver ticket 2.6)."""
    ids_validos = {faixa["track_id"] for faixa in faixas_resultado}

    validas = []
    divergentes = []
    for track_id in citadas:
        if track_id in ids_validos:
            if track_id not in validas:
                validas.append(track_id)
        else:
            divergentes.append(track_id)

    if divergentes:
        logger.warning(
            "faixas_citadas divergentes do resultado real da busca: %s (track_ids válidos: %s)",
            divergentes,
            sorted(ids_validos),
        )

    return AuditoriaResultado(citadas_validas=tuple(validas), divergentes=tuple(divergentes))
