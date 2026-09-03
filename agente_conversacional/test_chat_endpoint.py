import uuid
from fastapi.testclient import TestClient

from app import create_app


def test_criar_sessao_endpoint():
    """Ticket 3.1: Valida criação de session_id válido."""
    with TestClient(create_app()) as client:
        response = client.post("/session")

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    # Valida formato UUID
    parsed = uuid.UUID(data["session_id"])
    assert str(parsed) == data["session_id"]


def test_chat_endpoint_pagode():
    """Ticket 3.2: Valida resposta de turno para pagode."""
    session_id = str(uuid.uuid4())
    payload = {"session_id": session_id, "mensagem": "quero um pagode animado pro churrasco"}

    with TestClient(create_app()) as client:
        response = client.post("/chat", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert "mensagem" in data
    assert len(data["faixas"]) >= 1
    assert any("pagode" in f["genero"].lower() for f in data["faixas"])
    assert "track_id" in data["faixas"][0]
    assert "nome" in data["faixas"][0]
    assert "artista" in data["faixas"][0]


def test_chat_endpoint_rock():
    """Ticket 3.2: Valida resposta de turno para rock."""
    session_id = str(uuid.uuid4())
    payload = {"session_id": session_id, "mensagem": "manda um rock clássico dos anos 80"}

    with TestClient(create_app()) as client:
        response = client.post("/chat", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert any("rock" in f["genero"].lower() for f in data["faixas"])


def test_chat_endpoint_validation_error_missing_field():
    """Valida erro 422 ao omitir campos obrigatórios."""
    with TestClient(create_app()) as client:
        response = client.post("/chat", json={"mensagem": "olá"})

    assert response.status_code == 422
