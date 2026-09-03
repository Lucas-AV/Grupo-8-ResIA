from chat import gerador
from llm.errors import LLMCallError


def _faixa(track_id, nome="Nome", artista="Artista", genero="pop"):
    return {"track_id": track_id, "nome": nome, "artista": artista, "album": "Album", "genero": genero}


def test_gera_texto_e_faixas_citadas_a_partir_do_json_do_llm(monkeypatch):
    resultado = {"faixas": [_faixa("t1"), _faixa("t2")]}

    def fake_chamar_llm(mensagens, formato_json=None, timeout=None):
        return '{"texto": "Aqui vão duas faixas boas!", "faixas_citadas": ["t1", "t2"]}'

    monkeypatch.setattr("chat.gerador.chamar_llm", fake_chamar_llm)

    texto, citadas = gerador.gerar("quero pop", (), resultado)

    assert texto == "Aqui vão duas faixas boas!"
    assert citadas == ("t1", "t2")


def test_prompt_de_sistema_instrui_a_nunca_citar_faixa_fora_da_lista(monkeypatch):
    resultado = {"faixas": [_faixa("t1")]}
    calls = {}

    def fake_chamar_llm(mensagens, formato_json=None, timeout=None):
        calls["mensagens"] = mensagens
        return '{"texto": "ok", "faixas_citadas": ["t1"]}'

    monkeypatch.setattr("chat.gerador.chamar_llm", fake_chamar_llm)

    gerador.gerar("quero pop", (), resultado)

    system_prompt = calls["mensagens"][0]["content"]
    assert calls["mensagens"][0]["role"] == "system"
    assert "APENAS" in system_prompt
    assert "não esteja" in system_prompt or "nunca" in system_prompt.lower()


def test_resultado_vazio_nao_chama_llm_e_usa_template(monkeypatch):
    def _explode(*args, **kwargs):
        raise AssertionError("não deveria chamar o LLM com resultado vazio")

    monkeypatch.setattr("chat.gerador.chamar_llm", _explode)

    texto, citadas = gerador.gerar("algo raro", (), {"faixas": []})

    assert citadas == ()
    assert "não encontrei" in texto.lower()


def test_llm_falha_cai_pro_template_sem_quebrar_o_turno(monkeypatch):
    resultado = {"faixas": [_faixa("t1", nome="Faixa Segura")]}

    def fake_chamar_llm(mensagens, formato_json=None, timeout=None):
        raise LLMCallError("timeout")

    monkeypatch.setattr("chat.gerador.chamar_llm", fake_chamar_llm)

    texto, citadas = gerador.gerar("quero pop", (), resultado)

    assert "Faixa Segura" in texto
    assert citadas == ("t1",)


def test_llm_devolve_json_sem_texto_cai_pro_template(monkeypatch):
    resultado = {"faixas": [_faixa("t1", nome="Faixa Segura")]}

    def fake_chamar_llm(mensagens, formato_json=None, timeout=None):
        return '{"faixas_citadas": ["t1"]}'

    monkeypatch.setattr("chat.gerador.chamar_llm", fake_chamar_llm)

    texto, citadas = gerador.gerar("quero pop", (), resultado)

    assert "Faixa Segura" in texto
    assert citadas == ("t1",)


def test_llm_devolve_texto_nao_json_cai_pro_template(monkeypatch):
    resultado = {"faixas": [_faixa("t1", nome="Faixa Segura")]}

    def fake_chamar_llm(mensagens, formato_json=None, timeout=None):
        return "isso não é um JSON"

    monkeypatch.setattr("chat.gerador.chamar_llm", fake_chamar_llm)

    texto, citadas = gerador.gerar("quero pop", (), resultado)

    assert "Faixa Segura" in texto
    assert citadas == ("t1",)


def test_faixas_citadas_ignora_itens_que_nao_sao_string(monkeypatch):
    resultado = {"faixas": [_faixa("t1")]}

    def fake_chamar_llm(mensagens, formato_json=None, timeout=None):
        return '{"texto": "ok", "faixas_citadas": ["t1", 42, null]}'

    monkeypatch.setattr("chat.gerador.chamar_llm", fake_chamar_llm)

    _, citadas = gerador.gerar("quero pop", (), resultado)

    assert citadas == ("t1",)
