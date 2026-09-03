import os
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

_DEFAULT_MAX_REQUESTS = 20
_DEFAULT_WINDOW_SECONDS = 60


class RateLimiter:
    """Limitador de taxa em memoria, por sessao (fallback: IP) — ticket 8.4.

    Pronto pra virar dependency de POST /chat assim que esse endpoint
    existir (ticket 3.2, Epico 3); ainda nao esta montado em nenhuma rota
    porque esse endpoint nao existe.
    """

    def __init__(self, max_requests=_DEFAULT_MAX_REQUESTS, window_seconds=_DEFAULT_WINDOW_SECONDS):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits = defaultdict(deque)

    def allow(self, identifier, now=None):
        now = time.monotonic() if now is None else now
        hits = self._hits[identifier]
        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()
        if len(hits) >= self.max_requests:
            return False
        hits.append(now)
        return True

    def __call__(self, request: Request):
        identifier = request.query_params.get("session_id") or (
            request.client.host if request.client else "unknown"
        )
        if not self.allow(identifier):
            raise HTTPException(status_code=429, detail="limite de requisicoes excedido, tente novamente em instantes")


def _int_env(name, default):
    return int(os.environ.get(name, default))


chat_rate_limiter = RateLimiter(
    max_requests=_int_env("CHAT_RATE_LIMIT_MAX_REQUESTS", _DEFAULT_MAX_REQUESTS),
    window_seconds=_int_env("CHAT_RATE_LIMIT_WINDOW_SECONDS", _DEFAULT_WINDOW_SECONDS),
)
