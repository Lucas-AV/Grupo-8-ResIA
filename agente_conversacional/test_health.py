from llm.errors import LLMCallError
from llm.client import LLMBackendNotConfigured
from llm.health import check_llm_health


def test_check_llm_health_returns_available_when_call_succeeds(monkeypatch):
    monkeypatch.delenv("LLM_BACKEND", raising=False)
    monkeypatch.setattr("llm.health.chamar_llm", lambda mensagens, timeout=None: "pong")

    resultado = check_llm_health()

    assert resultado == {"disponivel": True, "backend": "ollama", "erro": None}


def test_check_llm_health_returns_unavailable_on_llmcallerror(monkeypatch):
    def fake_chamar_llm(mensagens, timeout=None):
        raise LLMCallError("Ollama fora do ar")

    monkeypatch.setattr("llm.health.chamar_llm", fake_chamar_llm)

    resultado = check_llm_health()

    assert resultado["disponivel"] is False
    assert "Ollama fora do ar" in resultado["erro"]


def test_check_llm_health_returns_unavailable_on_backend_not_configured(monkeypatch):
    def fake_chamar_llm(mensagens, timeout=None):
        raise LLMBackendNotConfigured("bogus")

    monkeypatch.setattr("llm.health.chamar_llm", fake_chamar_llm)

    resultado = check_llm_health()

    assert resultado["disponivel"] is False
    assert "bogus" in resultado["erro"]


def test_check_llm_health_reports_configured_backend_name(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "claude")
    monkeypatch.setattr("llm.health.chamar_llm", lambda mensagens, timeout=None: "pong")

    resultado = check_llm_health()

    assert resultado["backend"] == "claude"
