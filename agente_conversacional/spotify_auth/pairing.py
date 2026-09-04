"""Pareamento QR com aprovação no dispositivo que exibiu o código.

O QR leva um segredo aleatório de uso único, mas tokens só são gravados após a
aprovação explícita na sessão original. Assim uma foto encaminhada do QR não
consegue sequestrar a sessão silenciosamente.
"""
from __future__ import annotations

import secrets
import time
from dataclasses import dataclass


@dataclass
class Pairing:
    session_id: str
    secret: str
    expires_at: float
    tokens: dict | None = None


class PairingStore:
    def __init__(self, ttl_seconds: int = 180):
        self.ttl_seconds = ttl_seconds
        self._items: dict[str, Pairing] = {}

    def create(self, session_id: str) -> tuple[str, str]:
        self.cleanup()
        code, secret = secrets.token_urlsafe(18), secrets.token_urlsafe(32)
        self._items[code] = Pairing(session_id, secret, time.time() + self.ttl_seconds)
        return code, secret

    def get(self, code: str, secret: str | None = None) -> Pairing | None:
        self.cleanup()
        item = self._items.get(code)
        if item and (secret is None or secrets.compare_digest(item.secret, secret)):
            return item
        return None

    def consume(self, code: str) -> Pairing | None:
        self.cleanup()
        return self._items.pop(code, None)

    def cleanup(self) -> None:
        now = time.time()
        self._items = {key: value for key, value in self._items.items() if value.expires_at > now}
