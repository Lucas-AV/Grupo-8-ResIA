from datetime import UTC, datetime, timedelta

import pytest

from sessions.models import Track, TurnResult
from sessions.store import SessionNotFound, SessionStore


class Clock:
    def __init__(self):
        self.now = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)

    def __call__(self):
        return self.now

    def advance(self, **delta):
        self.now += timedelta(**delta)


def result_for_test():
    return TurnResult(
        mensagem="Uma recomendação válida.",
        faixas=(Track("track-1", "Nome", "Artista", "Álbum", "pop"),),
        diversidade_generos=1,
        cobertura_sessao=1.0,
        consulta_efetiva={"genero": "pop"},
        faixas_citadas=("track-1",),
    )


def test_create_initializes_empty_anonymous_session():
    store = SessionStore()

    first_id = store.create()
    second_id = store.create()
    context = store.get_context(first_id)

    assert first_id != second_id
    assert context.historico == ()
    assert context.perfil_usuario is None
    assert context.autenticada is False
    assert context.faixas_ja_mostradas == frozenset()


def test_commit_turn_updates_history_tracks_and_metrics():
    store = SessionStore()
    session_id = store.create()

    store.commit_turn(session_id, "quero pop", result_for_test())
    context = store.get_context(session_id)

    assert [message.role for message in context.historico] == ["usuario", "agente"]
    assert context.historico[1].faixas_citadas == ("track-1",)
    assert context.faixas_ja_mostradas == frozenset({"track-1"})
    assert context.metricas.diversidade_generos == 1
    assert context.metricas.cobertura_media == 1.0


def test_mark_authenticated_promotes_existing_session_without_losing_history():
    store = SessionStore()
    session_id = store.create()
    store.commit_turn(session_id, "quero pop", result_for_test())

    store.mark_authenticated(session_id, [0.2, 0.8])
    context = store.get_context(session_id)

    assert context.autenticada is True
    assert context.perfil_usuario == (0.2, 0.8)
    assert len(context.historico) == 2


def test_expired_session_is_purged_on_access():
    clock = Clock()
    store = SessionStore(timeout_minutes=30, clock=clock)
    session_id = store.create()

    clock.advance(minutes=30)

    with pytest.raises(SessionNotFound):
        store.get_history(session_id)
    assert store.count() == 0
