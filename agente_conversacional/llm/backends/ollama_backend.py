import os

import requests

from llm.errors import LLMCallError

_DEFAULT_BASE_URL = "http://localhost:11434"
_DEFAULT_MODEL = "qwen2.5:7b-instruct-q4_K_M"


def call(mensagens, formato_json=None, timeout=None):
    base_url = os.environ.get("OLLAMA_BASE_URL", _DEFAULT_BASE_URL).rstrip("/")
    model = os.environ.get("OLLAMA_MODEL", _DEFAULT_MODEL)

    payload = {"model": model, "messages": mensagens, "stream": False}
    if formato_json:
        payload["format"] = "json"

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
