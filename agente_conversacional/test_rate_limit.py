from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from rate_limit import RateLimiter


def test_allow_permits_up_to_max_requests_within_window():
    limiter = RateLimiter(max_requests=3, window_seconds=60)

    assert limiter.allow("sess-1", now=0) is True
    assert limiter.allow("sess-1", now=1) is True
    assert limiter.allow("sess-1", now=2) is True
    assert limiter.allow("sess-1", now=3) is False


def test_allow_tracks_identifiers_independently():
    limiter = RateLimiter(max_requests=1, window_seconds=60)

    assert limiter.allow("sess-1", now=0) is True
    assert limiter.allow("sess-2", now=0) is True
    assert limiter.allow("sess-1", now=0) is False


def test_allow_resets_after_window_elapses():
    limiter = RateLimiter(max_requests=1, window_seconds=60)

    assert limiter.allow("sess-1", now=0) is True
    assert limiter.allow("sess-1", now=30) is False
    assert limiter.allow("sess-1", now=61) is True


def _app_with_limiter(limiter):
    app = FastAPI()

    @app.get("/ping", dependencies=[Depends(limiter)])
    def ping():
        return {"ok": True}

    return app


def test_dependency_raises_429_when_limit_exceeded():
    limiter = RateLimiter(max_requests=1, window_seconds=60)

    with TestClient(_app_with_limiter(limiter)) as client:
        first = client.get("/ping?session_id=sess-1")
        second = client.get("/ping?session_id=sess-1")

    assert first.status_code == 200
    assert second.status_code == 429


def test_dependency_prefers_session_id_over_client_ip():
    limiter = RateLimiter(max_requests=1, window_seconds=60)

    with TestClient(_app_with_limiter(limiter)) as client:
        first = client.get("/ping?session_id=sess-A")
        second = client.get("/ping?session_id=sess-B")

    assert first.status_code == 200
    assert second.status_code == 200
