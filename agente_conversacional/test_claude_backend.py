import requests

from llm.backends import claude_backend
from llm.errors import LLMCallError


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_call_raises_when_api_key_missing(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    try:
        claude_backend.call([{"role": "user", "content": "oi"}], timeout=8)
        assert False, "deveria ter levantado LLMCallError"
    except LLMCallError as exc:
        assert "ANTHROPIC_API_KEY" in str(exc)


def test_call_returns_text_from_content_blocks(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("CLAUDE_MODEL", "claude-sonnet-5")
    captured = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return FakeResponse(200, {"content": [{"type": "text", "text": "boa pedida"}]})

    monkeypatch.setattr(claude_backend.requests, "post", fake_post)

    resultado = claude_backend.call([{"role": "user", "content": "oi"}], timeout=8)

    assert resultado == "boa pedida"
    assert captured["json"]["model"] == "claude-sonnet-5"
    assert captured["headers"]["x-api-key"] == "test-key"


def test_call_extracts_system_message_separately(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    captured = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["json"] = json
        return FakeResponse(200, {"content": [{"type": "text", "text": "ok"}]})

    monkeypatch.setattr(claude_backend.requests, "post", fake_post)

    mensagens = [
        {"role": "system", "content": "instrucao do sistema"},
        {"role": "user", "content": "oi"},
    ]
    claude_backend.call(mensagens, timeout=8)

    assert captured["json"]["system"] == "instrucao do sistema"
    assert captured["json"]["messages"] == [{"role": "user", "content": "oi"}]


def test_call_raises_llmcallerror_on_connection_error(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    def fake_post(url, json=None, headers=None, timeout=None):
        raise requests.exceptions.ConnectionError("recusado")

    monkeypatch.setattr(claude_backend.requests, "post", fake_post)

    try:
        claude_backend.call([{"role": "user", "content": "oi"}], timeout=8)
        assert False, "deveria ter levantado LLMCallError"
    except LLMCallError:
        pass


def test_call_raises_llmcallerror_on_non_200_status(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(
        claude_backend.requests,
        "post",
        lambda url, json=None, headers=None, timeout=None: FakeResponse(401),
    )

    try:
        claude_backend.call([{"role": "user", "content": "oi"}], timeout=8)
        assert False, "deveria ter levantado LLMCallError"
    except LLMCallError as exc:
        assert "401" in str(exc)


def test_call_raises_llmcallerror_when_text_missing(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(
        claude_backend.requests,
        "post",
        lambda url, json=None, headers=None, timeout=None: FakeResponse(200, {"content": []}),
    )

    try:
        claude_backend.call([{"role": "user", "content": "oi"}], timeout=8)
        assert False, "deveria ter levantado LLMCallError"
    except LLMCallError:
        pass
