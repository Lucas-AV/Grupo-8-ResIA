from datetime import UTC, datetime

from sessions.models import Message

from chat import extrator
from llm.errors import LLMCallError


def _msg(role, conteudo):
    return Message(role, conteudo, (), datetime(2026, 9, 3, tzinfo=UTC))


def test_extrai_consulta_de_resposta_json_pura(monkeypatch):
    calls = {}

    def fake_chamar_llm(mensagens, formato_json=None, timeout=None):
        calls["mensagens"] = mensagens
        calls["formato_json"] = formato_json
        return '{"genero": "pop", "energia": "alta", "valencia": null, ' \
               '"dancabilidade": null, "artista_referencia": null, ' \
               '"excluir_explicit": false, "n_resultados": 10}'

    monkeypatch.setattr("chat.extrator.chamar_llm", fake_chamar_llm)

    consulta = extrator.extrair_consulta("algo animado", historico=())

    assert consulta["genero"] == "pop"
    assert consulta["energia"] == "alta"
    assert calls["formato_json"] is True
    assert calls["mensagens"][0]["role"] == "system"
    assert calls["mensagens"][0]["content"] == extrator.SYSTEM_PROMPT_EXTRACAO_V1
    assert calls["mensagens"][-1] == {"role": "user", "content": "algo animado"}


def test_tolera_texto_ao_redor_do_json(monkeypatch):
    def fake_chamar_llm(mensagens, formato_json=None, timeout=None):
        return 'Claro, aqui está:\n{"genero": "jazz"}\nEspero ajudar!'

    monkeypatch.setattr("chat.extrator.chamar_llm", fake_chamar_llm)

    consulta = extrator.extrair_consulta("quero algo tipo jazz suave")

    assert consulta == {"genero": "jazz"}


def test_devolve_none_quando_llm_falha(monkeypatch):
    def fake_chamar_llm(mensagens, formato_json=None, timeout=None):
        raise LLMCallError("timeout")

    monkeypatch.setattr("chat.extrator.chamar_llm", fake_chamar_llm)

    assert extrator.extrair_consulta("qualquer coisa") is None


def test_devolve_none_quando_resposta_nao_tem_json(monkeypatch):
    def fake_chamar_llm(mensagens, formato_json=None, timeout=None):
        return "desculpe, não entendi"

    monkeypatch.setattr("chat.extrator.chamar_llm", fake_chamar_llm)

    assert extrator.extrair_consulta("qualquer coisa") is None


def test_historico_truncado_e_enviado_ao_llm(monkeypatch):
    calls = {}

    def fake_chamar_llm(mensagens, formato_json=None, timeout=None):
        calls["mensagens"] = mensagens
        return "{}"

    monkeypatch.setattr("chat.extrator.chamar_llm", fake_chamar_llm)

    historico = tuple(_msg("usuario", f"msg {i}") for i in range(10))
    extrator.extrair_consulta("nova mensagem", historico=historico)

    # system + 6 do historico truncado + 1 mensagem do usuario atual
    assert len(calls["mensagens"]) == 1 + 6 + 1
    assert calls["mensagens"][1]["content"] == "msg 4"
