import secrets
import threading
import time

_TTL_SECONDS = 5 * 60


class PairingStore:
    """Relay efêmero e de uso único: correlaciona um código de pareamento
    (mostrado como QR num dispositivo) com os tokens que outro dispositivo
    produz ao completar o OAuth. TTL curto, purge preguiçosa no read —
    mesmo padrão de agente_conversacional/sessions/store.py."""

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
            if entry is not None:
                entry["tokens"] = tokens

    def consume(self, code):
        with self._lock:
            self._purge_expired_locked()
            entry = self._entries.get(code)
            if entry is None or entry["tokens"] is None:
                return None
            del self._entries[code]
            return entry["tokens"]

    def _purge_expired_locked(self):
        now = self._clock()
        expired = [c for c, e in self._entries.items() if now - e["created_at"] >= _TTL_SECONDS]
        for c in expired:
            del self._entries[c]
