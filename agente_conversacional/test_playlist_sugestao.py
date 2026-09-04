"""Ticket 12.6 — sugestão de título/descrição de playlist via LLM, usada no
modal de "Salvar no Spotify" (ver playlist_sugestao_e_modal_de_confirmacao
spec). Nunca bloqueia a criação da playlist: qualquer falha (LLM
indisponível/timeout, JSON inválido) degrada pro nome/descrição padrão já
usados em spotify_auth/playlist.py."""

from chat import playlist_sugestao
from llm.errors import LLMCallError

_FAIXAS = [
    {"nome": "Deixa Acontecer", "artista": "Grupo Revelação", "genero": "pagode"},
    {"nome": "Pé Na Areia", "artista": "Diogo Nogueira", "genero": "pagode"},
]


def test_sugere_titulo_e_descricao_a_partir_da_resposta_json_do_llm(monkeypatch):
    calls = {}

    def fake_chamar_llm(mensagens, formato_json=None, timeout=None):
        calls["mensagens"] = mensagens
        calls["formato_json"] = formato_json
        return '{"titulo": "Pagode pra Domingo", "descricao": "Clássicos animados pro churrasco."}'

    monkeypatch.setattr("chat.playlist_sugestao.chamar_llm", fake_chamar_llm)

    sugestao = playlist_sugestao.sugerir_titulo_descricao(_FAIXAS)

    assert sugestao == {"titulo": "Pagode pra Domingo", "descricao": "Clássicos animados pro churrasco."}
    assert calls["formato_json"] is True
    assert calls["mensagens"][0]["role"] == "system"
    assert "Deixa Acontecer" in calls["mensagens"][-1]["content"]
    assert "Grupo Revelação" in calls["mensagens"][-1]["content"]


def test_tolera_texto_ao_redor_do_json(monkeypatch):
    def fake_chamar_llm(mensagens, formato_json=None, timeout=None):
        return 'Aqui está:\n{"titulo": "Rock Anos 80", "descricao": "Hinos clássicos."}\nEspero que goste!'

    monkeypatch.setattr("chat.playlist_sugestao.chamar_llm", fake_chamar_llm)

    sugestao = playlist_sugestao.sugerir_titulo_descricao(_FAIXAS)

    assert sugestao == {"titulo": "Rock Anos 80", "descricao": "Hinos clássicos."}


def test_degrada_pro_padrao_quando_llm_falha(monkeypatch):
    def fake_chamar_llm(mensagens, formato_json=None, timeout=None):
        raise LLMCallError("timeout")

    monkeypatch.setattr("chat.playlist_sugestao.chamar_llm", fake_chamar_llm)

    sugestao = playlist_sugestao.sugerir_titulo_descricao(_FAIXAS)

    assert sugestao == {"titulo": playlist_sugestao._NOME_PADRAO, "descricao": playlist_sugestao._DESCRICAO_PADRAO}


def test_degrada_pro_padrao_quando_resposta_nao_e_json_valido(monkeypatch):
    monkeypatch.setattr("chat.playlist_sugestao.chamar_llm", lambda *a, **kw: "isso não é JSON nenhum")

    sugestao = playlist_sugestao.sugerir_titulo_descricao(_FAIXAS)

    assert sugestao == {"titulo": playlist_sugestao._NOME_PADRAO, "descricao": playlist_sugestao._DESCRICAO_PADRAO}


def test_degrada_pro_padrao_quando_chave_individual_vem_vazia(monkeypatch):
    monkeypatch.setattr(
        "chat.playlist_sugestao.chamar_llm", lambda *a, **kw: '{"titulo": "", "descricao": "Só isso."}'
    )

    sugestao = playlist_sugestao.sugerir_titulo_descricao(_FAIXAS)

    assert sugestao["titulo"] == playlist_sugestao._NOME_PADRAO
    assert sugestao["descricao"] == "Só isso."


def test_sem_faixas_devolve_padrao_sem_chamar_o_llm(monkeypatch):
    def fake_chamar_llm(*args, **kwargs):
        raise AssertionError("nao deveria chamar o LLM sem faixas")

    monkeypatch.setattr("chat.playlist_sugestao.chamar_llm", fake_chamar_llm)

    sugestao = playlist_sugestao.sugerir_titulo_descricao([])

    assert sugestao == {"titulo": playlist_sugestao._NOME_PADRAO, "descricao": playlist_sugestao._DESCRICAO_PADRAO}
