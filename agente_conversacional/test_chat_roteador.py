from chat.roteador import rotear


def test_reconhece_genero_simples_sem_chamar_llm():
    match = rotear("quero country")

    assert match.tipo == "consulta"
    assert match.consulta["genero"] == "country"


def test_reconhece_genero_edm():
    match = rotear("toca umas eletronicas")

    assert match.tipo == "consulta"
    assert match.consulta["genero"] == "edm"


def test_reconhece_genero_classical():
    match = rotear("quero musica classica")

    assert match.tipo == "consulta"
    assert match.consulta["genero"] == "classical"


def test_reconhece_humor_energia_alta():
    match = rotear("algo mais animado")

    assert match.tipo == "consulta"
    assert match.consulta["energia"] == "alta"
    assert match.consulta["genero"] is None


def test_reconhece_humor_energia_baixa():
    match = rotear("quero algo mais calmo")

    assert match.tipo == "consulta"
    assert match.consulta["energia"] == "baixa"


def test_reconhece_valencia_triste():
    match = rotear("uma musica triste")

    assert match.tipo == "consulta"
    assert match.consulta["valencia"] == "triste"


def test_saudacao_nao_vira_busca():
    match = rotear("oi, tudo bem?")

    assert match.tipo == "saudacao"
    assert match.consulta is None


def test_saudacao_bom_dia():
    assert rotear("bom dia!").tipo == "saudacao"


def test_pedido_fora_de_escopo_nao_vira_busca():
    match = rotear("componha uma musica nova pra mim")

    assert match.tipo == "fora_escopo"


def test_mensagem_livre_e_longa_nao_e_resolvida_pelo_roteador():
    # Caso de uso 2 do pipeline: frase conversacional deve seguir pra
    # extracao via LLM, nao ser "roubada" pelo roteador.
    resultado = rotear("algo pra relaxar depois de um dia puxado")

    assert resultado is None


def test_mensagem_sem_nenhum_padrao_reconhecido_devolve_none():
    assert rotear("me surpreenda com alguma coisa diferente hoje por favor") is None


def test_mensagem_vazia_devolve_none():
    assert rotear("") is None
    assert rotear("   ") is None
    assert rotear(None) is None


def test_consulta_montada_tem_todas_as_chaves_do_schema():
    match = rotear("quero blues")

    assert set(match.consulta.keys()) == {
        "genero",
        "energia",
        "valencia",
        "dancabilidade",
        "artista_referencia",
        "excluir_explicit",
        "n_resultados",
    }
