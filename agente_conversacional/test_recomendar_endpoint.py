from fastapi.testclient import TestClient

import api.routes as api_routes
import app as app_module
from app import create_app


def client_for(monkeypatch):
    monkeypatch.setattr(
        app_module,
        "check_llm_health",
        lambda: {"disponivel": False, "backend": "ollama", "erro": "mock"},
    )
    return TestClient(create_app())


def _fake_resultado(**overrides):
    resultado = {
        "faixas": [
            {"track_id": "t1", "nome": "Musica 1", "artista": "Artista 1", "album": "Album 1", "genero": "pop"},
        ],
        "diversidade_generos": 1,
        "cobertura_sessao": 1.0,
        "consulta_efetiva": {"genero": "pop", "n_resultados": 10},
    }
    resultado.update(overrides)
    return resultado


def test_recomendar_nunca_toca_llm_e_chama_busca_direto(monkeypatch):
    """Criterio de aceite do ticket 12.3: funciona com zero LLM configurado —
    a rota so chama buscar_recomendacoes, nunca chat/contracts.TurnProcessor."""
    captured = {}

    def fake_buscar_recomendacoes(**kwargs):
        captured.update(kwargs)
        return _fake_resultado()

    monkeypatch.setattr(api_routes, "buscar_recomendacoes", fake_buscar_recomendacoes)

    with client_for(monkeypatch) as client:
        response = client.get("/recomendar", params={"genero": "pop", "energia": "alta"})

    assert response.status_code == 200
    body = response.json()
    assert body["faixas"] == [
        {
            "track_id": "t1",
            "nome": "Musica 1",
            "artista": "Artista 1",
            "album": "Album 1",
            "genero": "pop",
            "preview_url": None,
        }
    ]
    assert body["diversidade_generos"] == 1
    assert body["cobertura_sessao"] == 1.0
    assert body["consulta_efetiva"] == {"genero": "pop", "n_resultados": 10}
    assert captured["genero"] == "pop"
    assert captured["energia"] == "alta"


def test_recomendar_aceita_humor_como_alias_de_valencia(monkeypatch):
    captured = {}

    def fake_buscar_recomendacoes(**kwargs):
        captured.update(kwargs)
        return _fake_resultado()

    monkeypatch.setattr(api_routes, "buscar_recomendacoes", fake_buscar_recomendacoes)

    with client_for(monkeypatch) as client:
        response = client.get("/recomendar", params={"genero": "pop", "humor": "feliz"})

    assert response.status_code == 200
    assert captured["valencia"] == "feliz"


def test_recomendar_prioriza_valencia_explicita_sobre_humor(monkeypatch):
    captured = {}

    def fake_buscar_recomendacoes(**kwargs):
        captured.update(kwargs)
        return _fake_resultado()

    monkeypatch.setattr(api_routes, "buscar_recomendacoes", fake_buscar_recomendacoes)

    with client_for(monkeypatch) as client:
        response = client.get("/recomendar", params={"valencia": "triste", "humor": "feliz"})

    assert response.status_code == 200
    assert captured["valencia"] == "triste"


def test_recomendar_ignora_campos_extras_de_faixas_do_fallback_spotify(monkeypatch):
    """Faixas do fallback do Spotify (KAN-95) trazem uma chave extra `_origem`
    (ver recomendacao/spotify_fallback.py) — o schema TrackItem nao conhece
    esse campo e deve simplesmente ignora-lo, sem quebrar a resposta."""

    def fake_buscar_recomendacoes(**kwargs):
        return _fake_resultado(
            faixas=[
                {
                    "track_id": "t2",
                    "nome": "Musica Fallback",
                    "artista": "Artista 2",
                    "album": "Album 2",
                    "genero": "pop",
                    "_origem": "spotify_fallback",
                }
            ]
        )

    monkeypatch.setattr(api_routes, "buscar_recomendacoes", fake_buscar_recomendacoes)

    with client_for(monkeypatch) as client:
        response = client.get("/recomendar", params={"genero": "pop"})

    assert response.status_code == 200
    assert response.json()["faixas"] == [
        {
            "track_id": "t2",
            "nome": "Musica Fallback",
            "artista": "Artista 2",
            "album": "Album 2",
            "genero": "pop",
            "preview_url": None,
        }
    ]


def test_recomendar_funciona_sem_nenhum_parametro(monkeypatch):
    def fake_buscar_recomendacoes(**kwargs):
        assert kwargs["genero"] is None
        assert kwargs["energia"] is None
        assert kwargs["valencia"] is None
        return _fake_resultado(faixas=[], diversidade_generos=0, cobertura_sessao=0.0, consulta_efetiva={})

    monkeypatch.setattr(api_routes, "buscar_recomendacoes", fake_buscar_recomendacoes)

    with client_for(monkeypatch) as client:
        response = client.get("/recomendar")

    assert response.status_code == 200
    assert response.json()["faixas"] == []


def test_recomendar_funciona_de_verdade_contra_o_dataset_local():
    """Sem nenhum mock — garante que a integracao real com buscar_recomendacoes
    (ticket 1.3) funciona de ponta a ponta, sem LLM nenhum envolvido."""
    with TestClient(create_app()) as client:
        response = client.get("/recomendar", params={"n_resultados": 3})

    assert response.status_code == 200
    body = response.json()
    assert len(body["faixas"]) == 3
    assert "consulta_efetiva" in body
