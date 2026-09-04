import requests

from llm.backends import ollama_backend
from llm.errors import LLMCallError


class FakeResponse:
    def __init__(self, status_code=200, payload=None, raise_on_json=False):
        self.status_code = status_code
        self._payload = payload
        self._raise_on_json = raise_on_json

    def json(self):
        if self._raise_on_json:
            raise ValueError("resposta nao e JSON valido")
        return self._payload


def _mensagens():
    return [{"role": "user", "content": "quero pagode"}]


def test_call_returns_assistant_message_content(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")

    def fake_post(url, json=None, timeout=None):
        assert url == "http://localhost:11434/api/chat"
        assert json["model"] == "qwen2.5:7b-instruct"
        assert json["messages"] == _mensagens()
        assert json["stream"] is False
        assert timeout == 8
        return FakeResponse(200, {"message": {"role": "assistant", "content": "boa pedida"}})

    monkeypatch.setattr(ollama_backend.requests, "post", fake_post)

    resultado = ollama_backend.call(_mensagens(), timeout=8)

    assert resultado == "boa pedida"


def test_call_includes_format_json_when_requested(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["json"] = json
        return FakeResponse(200, {"message": {"content": "{}"}})

    monkeypatch.setattr(ollama_backend.requests, "post", fake_post)

    ollama_backend.call(_mensagens(), formato_json=True, timeout=8)

    assert captured["json"]["format"] == "json"


def test_call_omits_format_when_not_requested(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["json"] = json
        return FakeResponse(200, {"message": {"content": "ok"}})

    monkeypatch.setattr(ollama_backend.requests, "post", fake_post)

    ollama_backend.call(_mensagens(), timeout=8)

    assert "format" not in captured["json"]


def test_call_omits_options_when_not_configured(monkeypatch):
    monkeypatch.delenv("OLLAMA_NUM_CTX", raising=False)
    monkeypatch.delenv("OLLAMA_NUM_PREDICT", raising=False)
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["json"] = json
        return FakeResponse(200, {"message": {"content": "ok"}})

    monkeypatch.setattr(ollama_backend.requests, "post", fake_post)

    ollama_backend.call(_mensagens(), timeout=8)

    assert "options" not in captured["json"]


def test_call_includes_num_ctx_when_configured(monkeypatch):
    monkeypatch.setenv("OLLAMA_NUM_CTX", "2048")
    monkeypatch.delenv("OLLAMA_NUM_PREDICT", raising=False)
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["json"] = json
        return FakeResponse(200, {"message": {"content": "ok"}})

    monkeypatch.setattr(ollama_backend.requests, "post", fake_post)

    ollama_backend.call(_mensagens(), timeout=8)

    assert captured["json"]["options"] == {"num_ctx": 2048}


def test_call_includes_num_predict_when_configured(monkeypatch):
    monkeypatch.delenv("OLLAMA_NUM_CTX", raising=False)
    monkeypatch.setenv("OLLAMA_NUM_PREDICT", "512")
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["json"] = json
        return FakeResponse(200, {"message": {"content": "ok"}})

    monkeypatch.setattr(ollama_backend.requests, "post", fake_post)

    ollama_backend.call(_mensagens(), timeout=8)

    assert captured["json"]["options"] == {"num_predict": 512}


def test_call_raises_llmcallerror_on_connection_error(monkeypatch):
    def fake_post(url, json=None, timeout=None):
        raise requests.exceptions.ConnectionError("recusado")

    monkeypatch.setattr(ollama_backend.requests, "post", fake_post)

    try:
        ollama_backend.call(_mensagens(), timeout=8)
        assert False, "deveria ter levantado LLMCallError"
    except LLMCallError:
        pass


def test_call_raises_llmcallerror_on_timeout(monkeypatch):
    def fake_post(url, json=None, timeout=None):
        raise requests.exceptions.Timeout("estourou")

    monkeypatch.setattr(ollama_backend.requests, "post", fake_post)

    try:
        ollama_backend.call(_mensagens(), timeout=8)
        assert False, "deveria ter levantado LLMCallError"
    except LLMCallError:
        pass


def test_call_raises_llmcallerror_on_non_200_status(monkeypatch):
    monkeypatch.setattr(
        ollama_backend.requests, "post", lambda url, json=None, timeout=None: FakeResponse(500)
    )

    try:
        ollama_backend.call(_mensagens(), timeout=8)
        assert False, "deveria ter levantado LLMCallError"
    except LLMCallError as exc:
        assert "500" in str(exc)


def test_call_raises_llmcallerror_when_content_missing(monkeypatch):
    monkeypatch.setattr(
        ollama_backend.requests,
        "post",
        lambda url, json=None, timeout=None: FakeResponse(200, {"message": {}}),
    )

    try:
        ollama_backend.call(_mensagens(), timeout=8)
        assert False, "deveria ter levantado LLMCallError"
    except LLMCallError:
        pass
