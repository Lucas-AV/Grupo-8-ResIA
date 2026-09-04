"""Relay efêmero de pareamento por QR code (Épico 13 / 13.13).

Porta `spotify_explorer/pairing_store.py` pro produto real, sem alterações de
comportamento — mesmo TTL, mesma semântica de uso único. Correlaciona um
código mostrado como QR (escaneado por outro dispositivo) com os tokens que
esse outro dispositivo produz ao completar o OAuth, mesmo padrão de
`agente_conversacional/sessions/store.py`.
"""

import secrets
import threading
import time

_TTL_SECONDS = 5 * 60


class PairingStore:
    def __init__(self, clock=time.time):
        self._clock = clock
        self._lock = threading.RLock()
        self._entries = {}

    def create(self):
        with self._lock:
            self._purge_expired_locked()
            code = secrets.token_urlsafe(16)
            self._entries[code] = {"created_at": self._clock(), "tokens": None}
            return code

    def get_status(self, code):
        with self._lock:
            self._purge_expired_locked()
            entry = self._entries.get(code)
            if entry is None:
                return "not_found"
            return "completed" if entry["tokens"] is not None else "pending"

    def mark_completed(self, code, tokens):
        with self._lock:
            self._purge_expired_locked()
            entry = self._entries.get(code)
            if entry is None:
                return False
            entry["tokens"] = tokens
            return True

    def consume_if_completed(self, code):
        with self._lock:
            self._purge_expired_locked()
            entry = self._entries.get(code)
            if entry is None:
                return "not_found", None
            if entry["tokens"] is None:
                return "pending", None
            tokens = entry["tokens"]
            del self._entries[code]
            return "completed", tokens

    def _purge_expired_locked(self):
        now = self._clock()
        expired = [c for c, e in self._entries.items() if now - e["created_at"] >= _TTL_SECONDS]
        for c in expired:
            del self._entries[c]
