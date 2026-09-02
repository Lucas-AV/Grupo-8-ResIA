from fastapi.testclient import TestClient

from app import create_app
from llm.errors import LLMCallError


def test_app_boots_without_raising_when_llm_unavailable(monkeypatch):
    monkeypatch.setattr(
        "llm.health.chamar_llm",
        lambda mensagens, timeout=None: (_ for _ in ()).throw(LLMCallError("fora do ar")),
    )

    with TestClient(create_app()):
        pass


def test_health_endpoint_reflects_llm_availability(monkeypatch):
    monkeypatch.setattr("llm.health.chamar_llm", lambda mensagens, timeout=None: "pong")

    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["disponivel"] is True


def test_health_endpoint_reports_unavailable_without_500(monkeypatch):
    def fake_chamar_llm(mensagens, timeout=None):
        raise LLMCallError("fora do ar")

    monkeypatch.setattr("llm.health.chamar_llm", fake_chamar_llm)

    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["disponivel"] is False
