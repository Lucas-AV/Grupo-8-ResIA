import os

import requests

from llm.errors import LLMCallError

_DEFAULT_BASE_URL = "http://localhost:11434"
_DEFAULT_MODEL = "qwen2.5:7b-instruct-q4_K_M"


def _build_options():
    """Monta o `options` do Ollama a partir de env vars, se configuradas.

    Sem essas vars o payload nao inclui `options` (comportamento antigo
    preservado). `OLLAMA_NUM_CTX` menor reduz o KV cache e ajuda o modelo
    a caber inteiro na VRAM em vez de fazer offload parcial pra CPU.
    """
    options = {}

    num_ctx = os.environ.get("OLLAMA_NUM_CTX")
    if num_ctx:
        options["num_ctx"] = int(num_ctx)

    num_predict = os.environ.get("OLLAMA_NUM_PREDICT")
    if num_predict:
        options["num_predict"] = int(num_predict)

    return options


def call(mensagens, formato_json=None, timeout=None):
    base_url = os.environ.get("OLLAMA_BASE_URL", _DEFAULT_BASE_URL).rstrip("/")
    model = os.environ.get("OLLAMA_MODEL", _DEFAULT_MODEL)

    payload = {"model": model, "messages": mensagens, "stream": False}
    if formato_json:
        payload["format"] = "json"

    options = _build_options()
    if options:
        payload["options"] = options

    try:
        response = requests.post(f"{base_url}/api/chat", json=payload, timeout=timeout)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
        raise LLMCallError(f"falha ao conectar no Ollama em {base_url}: {exc}") from exc

    if response.status_code != 200:
        raise LLMCallError(f"Ollama respondeu HTTP {response.status_code}")

    try:
        body = response.json()
    except ValueError as exc:
        raise LLMCallError("resposta do Ollama nao e JSON valido") from exc

    content = body.get("message", {}).get("content")
    if not content:
        raise LLMCallError("resposta do Ollama nao trouxe message.content")

    return content
