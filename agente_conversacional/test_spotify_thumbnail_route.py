"""GET /spotify/thumbnail/{track_id} — usado pelo frontend pra mostrar a
capa do álbum nos cards de faixa recomendada (sem exigir login Spotify)."""

from fastapi.testclient import TestClient

from app import create_app
import app as app_module
from spotify_auth import thumbnail as thumbnail_client


def client_for(monkeypatch):
    monkeypatch.setattr(
        app_module,
        "check_llm_health",
        lambda: {"disponivel": False, "backend": "ollama", "erro": "mock"},
    )
    return TestClient(create_app())


def test_devolve_thumbnail_url_quando_encontrada(monkeypatch):
    monkeypatch.setattr(thumbnail_client, "buscar_thumbnail", lambda track_id, timeout=None: "https://img/abc.jpg")

    with client_for(monkeypatch) as client:
        response = client.get("/spotify/thumbnail/0VjIjW4GlUZAMYd2vXMi3b")

    assert response.status_code == 200
    assert response.json() == {"thumbnail_url": "https://img/abc.jpg"}


def test_devolve_thumbnail_url_none_quando_nao_encontrada(monkeypatch):
    monkeypatch.setattr(thumbnail_client, "buscar_thumbnail", lambda track_id, timeout=None: None)

    with client_for(monkeypatch) as client:
        response = client.get("/spotify/thumbnail/track-desconhecida")

    assert response.status_code == 200
    assert response.json() == {"thumbnail_url": None}
