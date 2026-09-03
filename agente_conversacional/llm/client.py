import os

from llm.backends import claude_backend, ollama_backend

_BACKENDS = {
    "ollama": ollama_backend,
    "claude": claude_backend,
}

_DEFAULT_TIMEOUT_SECONDS = 8.0


class LLMBackendNotConfigured(Exception):
    def __init__(self, backend_name):
        super().__init__(
            f"backend de LLM '{backend_name}' nao reconhecido "
            f"(opcoes: {', '.join(sorted(_BACKENDS))})"
        )
        self.backend_name = backend_name


def _resolve_timeout(timeout):
    if timeout is not None:
        return timeout
    return float(os.environ.get("LLM_TIMEOUT_SECONDS", _DEFAULT_TIMEOUT_SECONDS))


def chamar_llm(mensagens, formato_json=None, timeout=None):
    backend_name = os.environ.get("LLM_BACKEND", "ollama")
    backend = _BACKENDS.get(backend_name)
    if backend is None:
        raise LLMBackendNotConfigured(backend_name)

    resolved_timeout = _resolve_timeout(timeout)
    return backend.call(mensagens, formato_json=formato_json, timeout=resolved_timeout)
