"""Ticket 13.12 (KAN-121) — GET /youtube/preview, usado pelo frontend pra
achar um video_id do YouTube pra tocar como previa (fallback do preview_url
da Spotify, que vem null pra apps criados apos nov/2024)."""

from fastapi.testclient import TestClient

from app import create_app
import app as app_module
from youtube import client as youtube_client


def client_for(monkeypatch):
    monkeypatch.setattr(
        app_module,
        "check_llm_health",
        lambda: {"disponivel": False, "backend": "ollama", "erro": "mock"},
    )
    return TestClient(create_app())


def test_devolve_video_id_quando_encontrado(monkeypatch):
    monkeypatch.setattr(youtube_client, "buscar_video_id", lambda nome, artista, timeout=None: "abc123")

    with client_for(monkeypatch) as client:
        response = client.get("/youtube/preview", params={"nome": "Faixa", "artista": "Artista"})

    assert response.status_code == 200
    assert response.json() == {"video_id": "abc123"}


def test_devolve_video_id_none_quando_nao_encontrado(monkeypatch):
    monkeypatch.setattr(youtube_client, "buscar_video_id", lambda nome, artista, timeout=None: None)

    with client_for(monkeypatch) as client:
        response = client.get("/youtube/preview", params={"nome": "Faixa Obscura", "artista": "Artista X"})

    assert response.status_code == 200
    assert response.json() == {"video_id": None}


def test_artista_e_opcional(monkeypatch):
    recebido = {}

    def fake_buscar(nome, artista, timeout=None):
        recebido["nome"] = nome
        recebido["artista"] = artista
        return None

    monkeypatch.setattr(youtube_client, "buscar_video_id", fake_buscar)

    with client_for(monkeypatch) as client:
        response = client.get("/youtube/preview", params={"nome": "Faixa"})

    assert response.status_code == 200
    assert recebido == {"nome": "Faixa", "artista": None}


def test_nome_ausente_e_erro_de_validacao(monkeypatch):
    with client_for(monkeypatch) as client:
        response = client.get("/youtube/preview")

    assert response.status_code == 422
