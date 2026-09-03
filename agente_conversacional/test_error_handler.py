import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import handle_unhandled_exception


def _app_with_broken_route():
    app = FastAPI()
    app.exception_handler(Exception)(handle_unhandled_exception)

    @app.get("/boom")
    def boom():
        raise RuntimeError("boom, dados sensiveis aqui")

    return app


def test_unhandled_exception_returns_standardized_500_json():
    with TestClient(_app_with_broken_route(), raise_server_exceptions=False) as client:
        response = client.get("/boom")

    assert response.status_code == 500
    assert response.json() == {"erro": "erro interno do servidor"}
    assert "boom" not in response.text
    assert "Traceback" not in response.text


def test_unhandled_exception_is_logged_with_full_details(caplog):
    with caplog.at_level(logging.ERROR, logger="agente"):
        with TestClient(_app_with_broken_route(), raise_server_exceptions=False) as client:
            client.get("/boom")

    erro_logado = next(record for record in caplog.records if record.name == "agente")
    assert erro_logado.levelno == logging.ERROR
    assert erro_logado.exc_info is not None
    assert "boom, dados sensiveis aqui" in str(erro_logado.exc_info[1])
