import os

import requests

from llm.errors import LLMCallError

_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
_DEFAULT_MODEL = "claude-sonnet-5"
_DEFAULT_MAX_TOKENS = 1024


def _split_system(mensagens):
    system_parts = [m["content"] for m in mensagens if m.get("role") == "system"]
    chat_messages = [m for m in mensagens if m.get("role") != "system"]
    system = "\n".join(system_parts) if system_parts else None
    return system, chat_messages


def call(mensagens, formato_json=None, timeout=None):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise LLMCallError("ANTHROPIC_API_KEY nao configurada")

    model = os.environ.get("CLAUDE_MODEL", _DEFAULT_MODEL)
    system, chat_messages = _split_system(mensagens)

    payload = {"model": model, "max_tokens": _DEFAULT_MAX_TOKENS, "messages": chat_messages}
    if system:
        payload["system"] = system

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    try:
        response = requests.post(_ANTHROPIC_URL, json=payload, headers=headers, timeout=timeout)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
        raise LLMCallError(f"falha ao conectar na API da Claude: {exc}") from exc

    if response.status_code != 200:
        raise LLMCallError(f"API da Claude respondeu HTTP {response.status_code}")

    try:
        body = response.json()
    except ValueError as exc:
        raise LLMCallError("resposta da API da Claude nao e JSON valido") from exc

    text = "".join(
        block.get("text", "") for block in body.get("content", []) if block.get("type") == "text"
    )
    if not text:
        raise LLMCallError("resposta da API da Claude nao trouxe bloco de texto")

    return text
