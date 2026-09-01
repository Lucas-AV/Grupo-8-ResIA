"""Política central migrada do protótipo, agora aplicável a qualquer saída."""

from backend.modelos.chatbot import DecisaoConfianca, StatusResposta

LIMIAR_CONFIANCA_PADRAO = 0.90


def decidir_confianca(
    confianca: float,
    motivos: list[str] | None = None,
    limiar: float = LIMIAR_CONFIANCA_PADRAO,
) -> DecisaoConfianca:
    """Decide apenas o gate; o cálculo/calibração da confiança permanece TODO(Fase 4)."""

    status = StatusResposta.RESPONDER if confianca >= limiar else StatusResposta.REVISAO_HUMANA
    return DecisaoConfianca(
        confianca=confianca,
        limiar=limiar,
        status=status,
        motivos=motivos or [],
    )

