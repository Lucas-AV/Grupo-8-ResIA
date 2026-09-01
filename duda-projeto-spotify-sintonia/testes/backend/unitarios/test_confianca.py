from backend.agentes.confianca_hitl.politica import decidir_confianca
from backend.modelos.chatbot import StatusResposta


def test_bloqueia_abaixo_de_noventa_por_cento() -> None:
    assert decidir_confianca(0.899).status == StatusResposta.REVISAO_HUMANA


def test_libera_no_limiar() -> None:
    assert decidir_confianca(0.90).status == StatusResposta.RESPONDER

