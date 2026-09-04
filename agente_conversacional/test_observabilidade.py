import logging

from chat.observabilidade import registrar_turno


def test_log_minimo_por_turno_e_estruturado(caplog):
    with caplog.at_level(logging.INFO, logger="agente.chat.turno"):
        registrar_turno(rota="roteador", extracao="nao_necessaria", busca="sucesso", geracao="sucesso", auditoria="sucesso", resultado="sucesso", duracao_ms=12.4)

    assert "turno rota=roteador" in caplog.records[0].message
    assert "duracao_ms=12" in caplog.records[0].message
