import logging

from chat.auditoria import auditar_citacoes


def _faixa(track_id):
    return {"track_id": track_id, "nome": "N", "artista": "A", "album": "Al", "genero": "pop"}


def test_citacoes_todas_validas_passam_sem_divergencia():
    resultado = auditar_citacoes(["t1", "t2"], [_faixa("t1"), _faixa("t2")])

    assert resultado.citadas_validas == ("t1", "t2")
    assert resultado.divergentes == ()


def test_citacao_inventada_e_filtrada_e_reportada_como_divergente():
    resultado = auditar_citacoes(["t1", "faixa-inventada"], [_faixa("t1")])

    assert resultado.citadas_validas == ("t1",)
    assert resultado.divergentes == ("faixa-inventada",)


def test_divergencia_e_logada(caplog):
    with caplog.at_level(logging.WARNING, logger="agente.chat.auditoria"):
        auditar_citacoes(["fantasma"], [_faixa("t1")])

    assert any("divergentes" in registro.message for registro in caplog.records)


def test_duplicatas_nas_citacoes_nao_se_repetem_no_resultado():
    resultado = auditar_citacoes(["t1", "t1", "t2"], [_faixa("t1"), _faixa("t2")])

    assert resultado.citadas_validas == ("t1", "t2")


def test_lista_de_citacoes_vazia_nao_gera_divergencia():
    resultado = auditar_citacoes([], [_faixa("t1")])

    assert resultado.citadas_validas == ()
    assert resultado.divergentes == ()
