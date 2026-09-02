from llm.client import LLMBackendNotConfigured, chamar_llm


def test_chamar_llm_dispatches_to_ollama_backend_by_default(monkeypatch):
    monkeypatch.delenv("LLM_BACKEND", raising=False)
    monkeypatch.delenv("LLM_TIMEOUT_SECONDS", raising=False)
    calls = {}

    def fake_call(mensagens, formato_json=None, timeout=None):
        calls["mensagens"] = mensagens
        calls["formato_json"] = formato_json
        calls["timeout"] = timeout
        return "resposta do ollama"

    monkeypatch.setattr("llm.backends.ollama_backend.call", fake_call)

    resultado = chamar_llm([{"role": "user", "content": "oi"}])

    assert resultado == "resposta do ollama"
    assert calls["mensagens"] == [{"role": "user", "content": "oi"}]


def test_chamar_llm_dispatches_to_claude_backend_when_env_set(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "claude")
    calls = {}

    def fake_call(mensagens, formato_json=None, timeout=None):
        calls["called"] = True
        return "resposta do claude"

    monkeypatch.setattr("llm.backends.claude_backend.call", fake_call)

    resultado = chamar_llm([{"role": "user", "content": "oi"}])

    assert resultado == "resposta do claude"
    assert calls["called"] is True


def test_chamar_llm_raises_for_unknown_backend(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "bogus")

    try:
        chamar_llm([{"role": "user", "content": "oi"}])
        assert False, "deveria ter levantado LLMBackendNotConfigured"
    except LLMBackendNotConfigured as exc:
        assert "bogus" in str(exc)


def test_chamar_llm_uses_timeout_from_env_by_default(monkeypatch):
    monkeypatch.delenv("LLM_BACKEND", raising=False)
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "5")
    calls = {}

    def fake_call(mensagens, formato_json=None, timeout=None):
        calls["timeout"] = timeout
        return "ok"

    monkeypatch.setattr("llm.backends.ollama_backend.call", fake_call)

    chamar_llm([{"role": "user", "content": "oi"}])

    assert calls["timeout"] == 5.0


def test_chamar_llm_explicit_timeout_overrides_env(monkeypatch):
    monkeypatch.delenv("LLM_BACKEND", raising=False)
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "5")
    calls = {}

    def fake_call(mensagens, formato_json=None, timeout=None):
        calls["timeout"] = timeout
        return "ok"

    monkeypatch.setattr("llm.backends.ollama_backend.call", fake_call)

    chamar_llm([{"role": "user", "content": "oi"}], timeout=2)

    assert calls["timeout"] == 2


def test_chamar_llm_forwards_formato_json_flag(monkeypatch):
    monkeypatch.delenv("LLM_BACKEND", raising=False)
    calls = {}

    def fake_call(mensagens, formato_json=None, timeout=None):
        calls["formato_json"] = formato_json
        return "{}"

    monkeypatch.setattr("llm.backends.ollama_backend.call", fake_call)

    chamar_llm([{"role": "user", "content": "oi"}], formato_json=True)

    assert calls["formato_json"] is True
