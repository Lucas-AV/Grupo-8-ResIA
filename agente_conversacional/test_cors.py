from fastapi.testclient import TestClient

from app import create_app


def test_allowed_origin_gets_cors_headers_on_preflight(monkeypatch):
    monkeypatch.setenv("FRONTEND_URL", "http://127.0.0.1:5173")

    with TestClient(create_app()) as client:
        response = client.options(
            "/health",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_disallowed_origin_gets_no_cors_header(monkeypatch):
    monkeypatch.setenv("FRONTEND_URL", "http://127.0.0.1:5173")

    with TestClient(create_app()) as client:
        response = client.options(
            "/health",
            headers={
                "Origin": "http://evil.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert "access-control-allow-origin" not in response.headers


def test_supports_multiple_comma_separated_origins(monkeypatch):
    monkeypatch.setenv("FRONTEND_URL", "http://127.0.0.1:5173,https://demo.example.com")

    with TestClient(create_app()) as client:
        response = client.options(
            "/health",
            headers={
                "Origin": "https://demo.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.headers["access-control-allow-origin"] == "https://demo.example.com"
