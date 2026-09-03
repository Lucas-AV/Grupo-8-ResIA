import os

from llm.client import LLMBackendNotConfigured, chamar_llm
from llm.errors import LLMCallError

_PING_MENSAGENS = [{"role": "user", "content": "ping"}]


def check_llm_health(timeout=None):
    """Chamada trivial ao LLM configurado; nunca levanta excecao (ticket 0.4)."""
    backend = os.environ.get("LLM_BACKEND", "ollama")
    try:
        chamar_llm(_PING_MENSAGENS, timeout=timeout)
    except (LLMCallError, LLMBackendNotConfigured) as exc:
        return {"disponivel": False, "backend": backend, "erro": str(exc)}
    return {"disponivel": True, "backend": backend, "erro": None}
