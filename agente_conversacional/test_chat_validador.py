from chat.validador import validar_consulta


def test_genero_valido_e_normalizado_para_o_valor_real_do_dataset():
    resultado = validar_consulta({"genero": "BLUES"})

    assert resultado["genero"] == "blues"


def test_genero_invalido_vira_none_sem_rejeitar_a_consulta():
    resultado = validar_consulta({"genero": "genero-que-nao-existe", "energia": "alta"})

    assert resultado["genero"] is None
    assert resultado["energia"] == "alta"


def test_energia_valencia_dancabilidade_fora_do_enum_viram_none():
    resultado = validar_consulta(
        {"energia": "supimpa", "valencia": "meh", "dancabilidade": "muito alta"}
    )

    assert resultado["energia"] is None
    assert resultado["valencia"] is None
    assert resultado["dancabilidade"] is None


def test_energia_valencia_dancabilidade_validos_sao_normalizados_para_lowercase():
    resultado = validar_consulta({"energia": "ALTA", "valencia": "Triste", "dancabilidade": "baixa"})

    assert resultado["energia"] == "alta"
    assert resultado["valencia"] == "triste"
    assert resultado["dancabilidade"] == "baixa"


def test_artista_referencia_e_normalizado_como_no_matching_de_oauth():
    resultado = validar_consulta({"artista_referencia": "Ivete Sangalo!"})

    assert resultado["artista_referencia"] == "ivete sangalo"


def test_artista_referencia_vazio_ou_ausente_vira_none():
    assert validar_consulta({"artista_referencia": ""})["artista_referencia"] is None
    assert validar_consulta({})["artista_referencia"] is None
    assert validar_consulta({"artista_referencia": 123})["artista_referencia"] is None


def test_excluir_explicit_aceita_bool_e_string():
    assert validar_consulta({"excluir_explicit": True})["excluir_explicit"] is True
    assert validar_consulta({"excluir_explicit": False})["excluir_explicit"] is False
    assert validar_consulta({"excluir_explicit": "true"})["excluir_explicit"] is True
    assert validar_consulta({"excluir_explicit": "false"})["excluir_explicit"] is False
    assert validar_consulta({})["excluir_explicit"] is False


def test_n_resultados_absurdo_e_limitado_ao_teto():
    resultado = validar_consulta({"n_resultados": 500})

    assert resultado["n_resultados"] == 30


def test_n_resultados_negativo_ou_zero_e_limitado_ao_minimo():
    assert validar_consulta({"n_resultados": 0})["n_resultados"] == 1
    assert validar_consulta({"n_resultados": -5})["n_resultados"] == 1


def test_n_resultados_invalido_cai_no_padrao():
    assert validar_consulta({"n_resultados": "muitas"})["n_resultados"] == 10
    assert validar_consulta({})["n_resultados"] == 10


def test_campo_fora_do_dominio_e_ignorado_sem_quebrar():
    resultado = validar_consulta({"genero": "blues", "campo_inventado_pelo_llm": "qualquer coisa"})

    assert resultado["genero"] == "blues"
    assert "campo_inventado_pelo_llm" not in resultado


def test_consulta_nao_dict_devolve_schema_default_sem_quebrar():
    resultado = validar_consulta(None)

    assert resultado == {
        "genero": None,
        "energia": None,
        "valencia": None,
        "dancabilidade": None,
        "artista_referencia": None,
        "excluir_explicit": False,
        "n_resultados": 10,
    }


def test_resultado_sempre_tem_as_sete_chaves_do_schema():
    resultado = validar_consulta({"genero": "blues"})

    assert set(resultado.keys()) == {
        "genero",
        "energia",
        "valencia",
        "dancabilidade",
        "artista_referencia",
        "excluir_explicit",
        "n_resultados",
    }
