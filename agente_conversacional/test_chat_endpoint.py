"""Teste de integração ponta a ponta do Épico 2: POST /chat usando o
`ChatPipeline` de verdade (não um fake), com o LLM e o dataset mockados
— prova que app.py está com o pipeline real ligado (não mais
turn_processor=None) e que o turno completo funciona através da API."""

import pandas as pd
from fastapi.testclient import TestClient

import app as app_module
from app import create_app
from recomendacao.dataset import carregar_dataset
from recomendacao.indice import IndiceSimilaridade

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


def _linha(track_id, genero, popularity=50):
    return [
        track_id,
        "Artista",
        "Album",
        f"Faixa {track_id}",
        popularity,
        200000,
        False,
        0.5,
        0.5,
        1,
        -8.0,
        1,
        0.05,
        0.1,
        0.0,
        0.2,
        0.4,
        120.0,
        4,
        genero,
    ]


def _preparar_dataset(tmp_path, monkeypatch):
    linhas = [_linha("t1", "blues", popularity=90), _linha("t2", "blues", popularity=80)]
    df_csv = pd.DataFrame(linhas, columns=COLUNAS)
    caminho = tmp_path / "dataset.csv"
    df_csv.to_csv(caminho, index=True)

    df = carregar_dataset(caminho)
    indice = IndiceSimilaridade(df)
    monkeypatch.setattr("recomendacao.busca.carregar_dataset", lambda: df)
    monkeypatch.setattr("recomendacao.busca.construir_indice", lambda: indice)
    monkeypatch.setattr("chat.validador.carregar_dataset", lambda: df)


def _client(monkeypatch):
    monkeypatch.setattr(
        app_module,
        "check_llm_health",
        lambda: {"disponivel": False, "backend": "ollama", "erro": "mock"},
    )
    return TestClient(create_app())


def test_chat_usa_pipeline_real_por_padrao_quando_nenhum_processor_e_injetado(monkeypatch):
    app = create_app()
    assert app.state.turn_processor is not None
    assert type(app.state.turn_processor).__name__ == "ChatPipeline"


def test_turno_completo_via_roteador_e_geracao_llm(tmp_path, monkeypatch):
    _preparar_dataset(tmp_path, monkeypatch)

    def fake_call(mensagens, formato_json=None, timeout=None):
        return '{"texto": "Separei um blues bem gostoso pra você!", "faixas_citadas": ["t1", "t2"]}'

    monkeypatch.setattr("llm.backends.ollama_backend.call", fake_call)

    with _client(monkeypatch) as client:
        session_id = client.post("/session").json()["session_id"]
        response = client.post("/chat", json={"session_id": session_id, "mensagem": "quero blues"})
        history = client.get("/chat/historico", params={"session_id": session_id})

    assert response.status_code == 200
    body = response.json()
    assert body["mensagem"] == "Separei um blues bem gostoso pra você!"
    assert {f["track_id"] for f in body["faixas"]} == {"t1", "t2"}
    assert body["consulta_efetiva"]["genero"] == "blues"

    assert history.status_code == 200
    historico = history.json()["historico"]
    assert [m["role"] for m in historico] == ["usuario", "agente"]
    assert set(historico[1]["faixas_citadas"]) == {"t1", "t2"}


def test_turno_completo_via_extracao_llm_quando_roteador_nao_resolve(tmp_path, monkeypatch):
    _preparar_dataset(tmp_path, monkeypatch)

    def fake_call(mensagens, formato_json=None, timeout=None):
        sistema = mensagens[0]["content"]
        if "módulo de extração" in sistema:
            return '{"genero": "blues", "n_resultados": 10}'
        return '{"texto": "Achei um blues legal!", "faixas_citadas": ["t1"]}'

    monkeypatch.setattr("llm.backends.ollama_backend.call", fake_call)

    with _client(monkeypatch) as client:
        session_id = client.post("/session").json()["session_id"]
        mensagem = "estou num clima meio nostalgico hoje a noite gostaria de algo"
        response = client.post("/chat", json={"session_id": session_id, "mensagem": mensagem})

    assert response.status_code == 200
    assert response.json()["consulta_efetiva"]["genero"] == "blues"


def test_saudacao_via_api_nao_gera_erro_e_nao_traz_faixas(tmp_path, monkeypatch):
    _preparar_dataset(tmp_path, monkeypatch)

    def _explode(*args, **kwargs):
        raise AssertionError("saudação não deveria chamar o LLM")

    monkeypatch.setattr("llm.backends.ollama_backend.call", _explode)

    with _client(monkeypatch) as client:
        session_id = client.post("/session").json()["session_id"]
        response = client.post("/chat", json={"session_id": session_id, "mensagem": "oi!"})

    assert response.status_code == 200
    assert response.json()["faixas"] == []


def test_fallback_total_via_api_quando_llm_indisponivel(tmp_path, monkeypatch):
    _preparar_dataset(tmp_path, monkeypatch)

    from llm.errors import LLMCallError

    def fake_call(mensagens, formato_json=None, timeout=None):
        raise LLMCallError("indisponivel")

    monkeypatch.setattr("llm.backends.ollama_backend.call", fake_call)

    with _client(monkeypatch) as client:
        session_id = client.post("/session").json()["session_id"]
        mensagem = "estou num clima meio nostalgico hoje a noite gostaria de algo"
        response = client.post("/chat", json={"session_id": session_id, "mensagem": mensagem})

    assert response.status_code == 200
    body = response.json()
    assert body["faixas"] == []
    assert "não entendi" in body["mensagem"].lower()
