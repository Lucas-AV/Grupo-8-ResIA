from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi.testclient import TestClient

from app import create_app
from chat.contracts import PipelineUnavailableError
from sessions.models import Track, TurnResult
from sessions.store import SessionStore
import api.routes as routes_module
import app as app_module


class Clock:
    def __init__(self):
        self.now = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)

    def __call__(self):
        return self.now

    def advance(self, **delta):
        self.now += timedelta(**delta)


class FakeProcessor:
    def __init__(self):
        self.contexts = []

    def process(self, mensagem, contexto):
        self.contexts.append(contexto)
        return TurnResult(
            mensagem=f"Sugestões para: {mensagem}",
            faixas=(Track("track-1", "Nome", "Artista", "Álbum", "pop"),),
            diversidade_generos=1,
            cobertura_sessao=1.0,
            consulta_efetiva={"genero": "pop"},
            faixas_citadas=("track-1",),
        )


class UnavailableProcessor:
    def process(self, mensagem, contexto):
        raise PipelineUnavailableError()


def client_for(monkeypatch, store=None, processor=None):
    monkeypatch.setattr(
        app_module,
        "check_llm_health",
        lambda: {"disponivel": False, "backend": "ollama", "erro": "mock"},
    )
    return TestClient(create_app(session_store=store, turn_processor=processor))


def test_session_endpoint_returns_uuid_and_empty_history(monkeypatch):
    with client_for(monkeypatch) as client:
        response = client.post("/session")
        session_id = response.json()["session_id"]
        history = client.get("/chat/historico", params={"session_id": session_id})

    assert response.status_code == 200
    assert str(UUID(session_id)) == session_id
    assert history.status_code == 200
    assert history.json() == {"session_id": session_id, "historico": []}


def test_chat_uses_processor_and_persists_auditable_history(monkeypatch):
    processor = FakeProcessor()
    with client_for(monkeypatch, processor=processor) as client:
        session_id = client.post("/session").json()["session_id"]
        response = client.post("/chat", json={"session_id": session_id, "mensagem": "  quero pop  "})
        second_response = client.post("/chat", json={"session_id": session_id, "mensagem": "mais uma"})
        history = client.get("/chat/historico", params={"session_id": session_id})

    assert response.status_code == 200
    assert response.json()["faixas"][0]["track_id"] == "track-1"
    assert response.json()["consulta_efetiva"] == {"genero": "pop"}
    assert processor.contexts[0].faixas_ja_mostradas == frozenset()
    assert processor.contexts[1].faixas_ja_mostradas == frozenset({"track-1"})
    assert second_response.status_code == 200
    assert [message["role"] for message in history.json()["historico"]] == [
        "usuario",
        "agente",
        "usuario",
        "agente",
    ]
    assert history.json()["historico"][1]["faixas_citadas"] == ["track-1"]


def test_historico_reconstroi_cards_de_faixa_das_faixas_citadas(monkeypatch):
    """Ticket 4.6/KAN-73: antes disso GET /chat/historico so devolvia
    faixas_citadas (IDs) — o frontend nunca conseguia remontar os cards de
    faixa ao restaurar o historico (sessao/reload). Agora `faixas` traz os
    metadados completos, resolvidos por buscar_faixa_por_id."""
    monkeypatch.setattr(
        routes_module,
        "buscar_faixa_por_id",
        lambda track_id: {"track_id": track_id, "nome": "Nome", "artista": "Artista", "album": "Álbum", "genero": "pop"}
        if track_id == "track-1"
        else None,
    )
    with client_for(monkeypatch, processor=FakeProcessor()) as client:
        session_id = client.post("/session").json()["session_id"]
        client.post("/chat", json={"session_id": session_id, "mensagem": "quero pop"})
        history = client.get("/chat/historico", params={"session_id": session_id})

    mensagem_agente = history.json()["historico"][1]
    assert mensagem_agente["faixas_citadas"] == ["track-1"]
    assert mensagem_agente["faixas"] == [
        {"track_id": "track-1", "nome": "Nome", "artista": "Artista", "album": "Álbum", "genero": "pop"}
    ]


def test_historico_omite_faixa_nao_encontrada_no_dataset(monkeypatch):
    """Faixa citada que nao existe mais no dataset local (ex.: veio do
    fallback da Spotify Search API) — omitida de `faixas`, sem quebrar o
    resto da resposta."""
    monkeypatch.setattr(routes_module, "buscar_faixa_por_id", lambda track_id: None)
    with client_for(monkeypatch, processor=FakeProcessor()) as client:
        session_id = client.post("/session").json()["session_id"]
        client.post("/chat", json={"session_id": session_id, "mensagem": "quero pop"})
        history = client.get("/chat/historico", params={"session_id": session_id})

    mensagem_agente = history.json()["historico"][1]
    assert mensagem_agente["faixas_citadas"] == ["track-1"]
    assert mensagem_agente["faixas"] == []


def test_chat_rejects_blank_message_and_unknown_session(monkeypatch):
    with client_for(monkeypatch, processor=FakeProcessor()) as client:
        blank = client.post("/chat", json={"session_id": "any", "mensagem": "   "})
        unknown = client.post("/chat", json={"session_id": "missing", "mensagem": "oi"})

    assert blank.status_code == 422
    assert unknown.status_code == 404
    assert unknown.json()["detail"]["codigo"] == "sessao_invalida"


def test_pipeline_unavailable_never_creates_partial_history(monkeypatch):
    with client_for(monkeypatch, processor=UnavailableProcessor()) as client:
        session_id = client.post("/session").json()["session_id"]
        response = client.post("/chat", json={"session_id": session_id, "mensagem": "oi"})
        history = client.get("/chat/historico", params={"session_id": session_id})

    assert response.status_code == 503
    assert response.json()["detail"]["codigo"] == "pipeline_indisponivel"
    assert history.json()["historico"] == []


def test_expired_session_returns_stable_not_found_response(monkeypatch):
    clock = Clock()
    store = SessionStore(timeout_minutes=30, clock=clock)
    with client_for(monkeypatch, store=store, processor=FakeProcessor()) as client:
        session_id = client.post("/session").json()["session_id"]
        clock.advance(minutes=30)
        response = client.get("/chat/historico", params={"session_id": session_id})

    assert response.status_code == 404
    assert response.json()["detail"]["codigo"] == "sessao_invalida"
