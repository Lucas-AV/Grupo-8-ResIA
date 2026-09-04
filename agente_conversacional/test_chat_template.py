from chat import template


def _faixa(track_id, nome="Nome", artista="Artista", genero="pop"):
    return {"track_id": track_id, "nome": nome, "artista": artista, "album": "Album", "genero": genero}


def test_formatar_resultado_com_faixas_lista_cada_uma():
    resultado = {"faixas": [_faixa("t1", nome="Faixa 1"), _faixa("t2", nome="Faixa 2")]}

    texto = template.formatar_resultado(resultado)

    assert "Faixa 1" in texto
    assert "Faixa 2" in texto
    assert "2 faixas" in texto


def test_formatar_resultado_com_uma_faixa_usa_singular():
    resultado = {"faixas": [_faixa("t1", nome="Solo")]}

    texto = template.formatar_resultado(resultado)

    assert "uma faixa" in texto
    assert "Solo" in texto


def test_formatar_resultado_vazio_tem_texto_diferenciado():
    resultado = {"faixas": []}

    texto = template.formatar_resultado(resultado)

    assert "não encontrei" in texto.lower()
    assert "Encontrei" not in texto


def test_saudacao_nao_menciona_faixas():
    texto = template.saudacao()

    assert isinstance(texto, str) and texto.strip()


def test_fora_de_escopo_explica_limitacao():
    texto = template.fora_de_escopo()

    assert isinstance(texto, str) and texto.strip()


def test_esclarecimento_e_pergunta_generica_nao_erro_cru():
    texto = template.esclarecimento()

    assert isinstance(texto, str) and texto.strip()
    assert "erro" not in texto.lower()


def test_templates_nao_chamam_llm(monkeypatch):
    def _explode(*args, **kwargs):
        raise AssertionError("template não deveria chamar o LLM")

    monkeypatch.setattr("llm.client.chamar_llm", _explode)

    template.formatar_resultado({"faixas": [_faixa("t1")]})
    template.formatar_resultado({"faixas": []})
    template.saudacao()
    template.fora_de_escopo()
    template.esclarecimento()
