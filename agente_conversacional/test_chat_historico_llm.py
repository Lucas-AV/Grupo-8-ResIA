from sessions.models import Message
from datetime import UTC, datetime

from chat.historico_llm import historico_para_mensagens, truncar_historico


def _msg(role, conteudo):
    return Message(role, conteudo, (), datetime(2026, 9, 3, tzinfo=UTC))


def test_truncar_historico_mantem_so_as_ultimas_n_mensagens():
    historico = tuple(_msg("usuario", f"msg {i}") for i in range(10))

    truncado = truncar_historico(historico, limite=6)

    assert len(truncado) == 6
    assert [m.conteudo for m in truncado] == [f"msg {i}" for i in range(4, 10)]


def test_truncar_historico_curto_fica_intacto():
    historico = (_msg("usuario", "oi"),)

    assert truncar_historico(historico, limite=6) == historico


def test_truncar_historico_vazio_ou_none_nao_quebra():
    assert truncar_historico((), limite=6) == ()
    assert truncar_historico(None, limite=6) == ()


def test_historico_para_mensagens_traduz_papeis():
    historico = (
        _msg("usuario", "quero pop"),
        _msg("agente", "aqui estão algumas faixas"),
        _msg("sistema", "nota interna"),
    )

    mensagens = historico_para_mensagens(historico)

    assert mensagens == [
        {"role": "user", "content": "quero pop"},
        {"role": "assistant", "content": "aqui estão algumas faixas"},
        {"role": "system", "content": "nota interna"},
    ]
