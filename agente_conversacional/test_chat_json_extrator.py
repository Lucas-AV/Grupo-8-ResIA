from chat.json_extrator import extrair_primeiro_json


def test_extrai_json_puro():
    assert extrair_primeiro_json('{"genero": "pop"}') == {"genero": "pop"}


def test_extrai_json_cercado_de_texto_livre():
    texto = 'Claro! Aqui está o que você pediu:\n{"genero": "pop", "n_resultados": 5}\nEspero ajudar!'
    assert extrair_primeiro_json(texto) == {"genero": "pop", "n_resultados": 5}


def test_extrai_json_dentro_de_bloco_markdown():
    texto = '```json\n{"genero": "rock"}\n```'
    assert extrair_primeiro_json(texto) == {"genero": "rock"}


def test_devolve_none_quando_nao_ha_json_valido():
    assert extrair_primeiro_json("não sei o que você quer dizer") is None


def test_devolve_none_para_entrada_nao_string():
    assert extrair_primeiro_json(None) is None
    assert extrair_primeiro_json(42) is None


def test_ignora_chave_solta_e_acha_o_primeiro_objeto_valido():
    texto = 'texto com { chave solta e depois {"genero": "jazz"} no meio'
    assert extrair_primeiro_json(texto) == {"genero": "jazz"}


def test_json_aninhado_e_extraido_inteiro():
    texto = 'resposta: {"texto": "oi", "faixas_citadas": ["a", "b"]} fim'
    assert extrair_primeiro_json(texto) == {"texto": "oi", "faixas_citadas": ["a", "b"]}
