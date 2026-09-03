import pandas as pd
import pytest

from chat.pipeline import ChatPipeline
from llm.errors import LLMCallError
from recomendacao.dataset import carregar_dataset
from recomendacao.indice import IndiceSimilaridade
from sessions.models import SessionContext, SessionMetrics

COLUNAS = [
    "track_id",
    "artists",
    "album_name",
    "track_name",
    "popularity",
    "duration_ms",
    "explicit",
    "danceability",
    "energy",
    "key",
    "loudness",
    "mode",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "time_signature",
    "track_genre",
]


def _linha(track_id, genero, artists="Artista", popularity=50, explicit=False, **audio):
    padrao = {
        "danceability": 0.5,
        "energy": 0.5,
        "loudness": -8.0,
        "speechiness": 0.05,
        "acousticness": 0.1,
        "instrumentalness": 0.0,
        "liveness": 0.2,
        "valence": 0.4,
        "tempo": 120.0,
    }
    padrao.update(audio)
    return [
        track_id,
        artists,
        "Album",
        f"Faixa {track_id}",
        popularity,
        200000,
        explicit,
        padrao["danceability"],
        padrao["energy"],
        1,
        padrao["loudness"],
        1,
        padrao["speechiness"],
        padrao["acousticness"],
        padrao["instrumentalness"],
        padrao["liveness"],
        padrao["valence"],
        padrao["tempo"],
        4,
        genero,
    ]


def _preparar(tmp_path, linhas, monkeypatch):
    df_csv = pd.DataFrame(linhas, columns=COLUNAS)
    caminho = tmp_path / "dataset.csv"
    df_csv.to_csv(caminho, index=True)

    df = carregar_dataset(caminho)
    indice = IndiceSimilaridade(df)
    monkeypatch.setattr("recomendacao.busca.carregar_dataset", lambda: df)
    monkeypatch.setattr("recomendacao.busca.construir_indice", lambda: indice)
    monkeypatch.setattr("chat.validador.carregar_dataset", lambda: df)
    return df


def _contexto(historico=()):
    return SessionContext(
        session_id="s1",
        historico=historico,
        perfil_usuario=None,
        autenticada=False,
        faixas_ja_mostradas=frozenset(),
        metricas=SessionMetrics(0, 0.0, 0),
    )


def _fake_llm_por_estagio(respostas, chamadas):
    """Fake pro backend do ollama que decide o que devolver olhando o
    prompt de sistema — evita ter que monkeypatchar `chamar_llm` em cada
    módulo (extrator/gerador) separadamente."""

    def fake_call(mensagens, formato_json=None, timeout=None):
        chamadas.append(mensagens)
        sistema = mensagens[0]["content"]
        if "módulo de extração" in sistema:
            return respostas["extracao"]
        if "módulo de geração" in sistema:
            return respostas["geracao"]
        raise AssertionError("prompt de sistema inesperado")

    return fake_call


def test_roteador_resolve_e_gera_resposta_via_llm(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "blues", popularity=90), _linha("t2", "blues", popularity=80)], monkeypatch)
    chamadas = []
    fake_call = _fake_llm_por_estagio(
        {"geracao": '{"texto": "Separei um blues bem gostoso!", "faixas_citadas": ["t1", "t2"]}'},
        chamadas,
    )
    monkeypatch.setattr("llm.backends.ollama_backend.call", fake_call)

    resultado = ChatPipeline().process("quero blues", _contexto())

    assert resultado.mensagem == "Separei um blues bem gostoso!"
    assert {f.track_id for f in resultado.faixas} == {"t1", "t2"}
    assert set(resultado.faixas_citadas) == {"t1", "t2"}
    assert resultado.consulta_efetiva["genero"] == "blues"
    # roteador resolveu -> só a geração deveria ter chamado o LLM
    assert len(chamadas) == 1


def test_extracao_via_llm_e_usada_quando_roteador_nao_resolve(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "blues", popularity=90)], monkeypatch)
    chamadas = []
    fake_call = _fake_llm_por_estagio(
        {
            "extracao": '{"genero": "blues", "energia": null, "valencia": null, '
            '"dancabilidade": null, "artista_referencia": null, '
            '"excluir_explicit": false, "n_resultados": 10}',
            "geracao": '{"texto": "Achei um blues!", "faixas_citadas": ["t1"]}',
        },
        chamadas,
    )
    monkeypatch.setattr("llm.backends.ollama_backend.call", fake_call)

    mensagem_longa = "estou num clima meio nostalgico hoje a noite gostaria de algo"
    resultado = ChatPipeline().process(mensagem_longa, _contexto())

    assert resultado.consulta_efetiva["genero"] == "blues"
    assert len(chamadas) == 2  # extração + geração


def test_fallback_total_nunca_chama_busca(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "blues")], monkeypatch)

    def fake_call(mensagens, formato_json=None, timeout=None):
        raise LLMCallError("indisponivel")

    monkeypatch.setattr("llm.backends.ollama_backend.call", fake_call)

    def _explode(*args, **kwargs):
        raise AssertionError("buscar_recomendacoes não deveria ser chamado no fallback total")

    monkeypatch.setattr("chat.pipeline.buscar_recomendacoes", _explode)

    mensagem_longa = "estou num clima meio nostalgico hoje a noite gostaria de algo"
    resultado = ChatPipeline().process(mensagem_longa, _contexto())

    assert resultado.faixas == ()
    assert resultado.consulta_efetiva == {}
    assert "não entendi" in resultado.mensagem.lower()


def test_saudacao_nao_chama_busca_nem_llm(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "blues")], monkeypatch)

    def _explode(*args, **kwargs):
        raise AssertionError("não deveria chamar nem busca nem LLM pra saudação")

    monkeypatch.setattr("chat.pipeline.buscar_recomendacoes", _explode)
    monkeypatch.setattr("llm.backends.ollama_backend.call", _explode)

    resultado = ChatPipeline().process("oi, tudo bem?", _contexto())

    assert resultado.faixas == ()
    assert resultado.mensagem


def test_fora_de_escopo_nao_chama_busca(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "blues")], monkeypatch)

    def _explode(*args, **kwargs):
        raise AssertionError("não deveria chamar busca pra pedido fora de escopo")

    monkeypatch.setattr("chat.pipeline.buscar_recomendacoes", _explode)

    resultado = ChatPipeline().process("componha uma musica nova pra mim", _contexto())

    assert resultado.faixas == ()


def test_geracao_indisponivel_cai_pro_template_sem_quebrar_turno(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "blues", popularity=90)], monkeypatch)

    def fake_call(mensagens, formato_json=None, timeout=None):
        raise LLMCallError("timeout na geracao")

    monkeypatch.setattr("llm.backends.ollama_backend.call", fake_call)

    resultado = ChatPipeline().process("quero blues", _contexto())

    assert resultado.faixas != ()
    assert resultado.faixas_citadas == tuple(f.track_id for f in resultado.faixas)
    assert "Encontrei" in resultado.mensagem


def test_citacao_inventada_pelo_llm_e_filtrada_do_resultado_final(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "blues", popularity=90)], monkeypatch)
    chamadas = []
    fake_call = _fake_llm_por_estagio(
        {"geracao": '{"texto": "aqui está!", "faixas_citadas": ["t1", "faixa-que-nao-existe"]}'},
        chamadas,
    )
    monkeypatch.setattr("llm.backends.ollama_backend.call", fake_call)

    resultado = ChatPipeline().process("quero blues", _contexto())

    assert resultado.faixas_citadas == ("t1",)


def test_resultado_vazio_da_busca_usa_template_sem_chamar_llm_de_geracao(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "blues", explicit=True, popularity=90)], monkeypatch)

    def _explode(*args, **kwargs):
        raise AssertionError("não deveria chamar o LLM quando a busca não acha nada")

    monkeypatch.setattr("llm.backends.ollama_backend.call", _explode)

    resultado = ChatPipeline().process("quero blues sem palavrao", _contexto())

    assert resultado.faixas == ()
    assert "não encontrei" in resultado.mensagem.lower()
