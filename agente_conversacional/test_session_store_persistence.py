"""Sessões sobrevivendo a um restart do processo — antes disso, SessionStore
era um dict Python puro (`sessions/store.py`), então todo restart do
servidor (deploy, crash, ou só reiniciar o uvicorn em dev) apagava todas as
sessões: o navegador continuava com o session_id salvo, mas o backend não
reconhecia mais — GET /chat/historico caía em 404 e o frontend descartava o
cache local também (ver app.js's carregarHistoricoInicial), como se a
conversa tivesse "descarregado".

Estes testes cobrem especificamente a persistência entre instâncias
(simulando um restart: uma segunda instância de SessionStore apontando pro
mesmo arquivo precisa enxergar o que a primeira gravou) — os testes de
comportamento de sessão em si (criação, expiração, etc.) continuam em
test_session_store.py, inalterados, usando o default em memória."""

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


def _resultado():
    return TurnResult(
        mensagem="Uma recomendação válida.",
        faixas=(Track("track-1", "Nome", "Artista", "Álbum", "pop"),),
        diversidade_generos=1,
        cobertura_sessao=1.0,
        consulta_efetiva={"genero": "pop"},
        faixas_citadas=("track-1",),
    )


def test_sessao_sobrevive_a_uma_nova_instancia_apontando_pro_mesmo_arquivo(tmp_path):
    db_path = str(tmp_path / "sessions.db")
    store_antes_do_restart = SessionStore(db_path=db_path)
    session_id = store_antes_do_restart.create()
    store_antes_do_restart.commit_turn(session_id, "quero pop", _resultado())
    store_antes_do_restart.mark_authenticated(session_id, [0.2, 0.8])

    # Simula o restart: nova instancia, mesmo arquivo, nenhum estado em memoria compartilhado.
    store_depois_do_restart = SessionStore(db_path=db_path)
    context = store_depois_do_restart.get_context(session_id)

    assert context.session_id == session_id
    assert [m.role for m in context.historico] == ["usuario", "agente"]
    assert context.historico[1].faixas_citadas == ("track-1",)
    assert context.faixas_ja_mostradas == frozenset({"track-1"})
    assert context.autenticada is True
    assert context.perfil_usuario == (0.2, 0.8)
    assert context.metricas.diversidade_generos == 1
    assert context.metricas.cobertura_media == 1.0


def test_get_history_sobrevive_a_uma_nova_instancia(tmp_path):
    db_path = str(tmp_path / "sessions.db")
    session_id = SessionStore(db_path=db_path).create()
    SessionStore(db_path=db_path).commit_turn(session_id, "quero rock", _resultado())

    historico = SessionStore(db_path=db_path).get_history(session_id)

    assert len(historico) == 2
    assert historico[0].conteudo == "quero rock"


def test_sessao_expirada_continua_expirada_apos_restart(tmp_path):
    db_path = str(tmp_path / "sessions.db")
    clock = Clock()
    session_id = SessionStore(db_path=db_path, timeout_minutes=30, clock=clock).create()

    clock.advance(minutes=31)

    # Nova instancia, "relogio" independente (mesmo clock object aqui só por
    # conveniência do teste) — o que importa e que o last_activity persistido
    # e usado pra decidir expiracao, nao um cache em memoria.
    store_depois = SessionStore(db_path=db_path, timeout_minutes=30, clock=clock)
    with pytest.raises(SessionNotFound):
        store_depois.get_context(session_id)


def test_construtor_sem_db_path_continua_efemero_em_memoria():
    # Sem db_path explicito, o default e :memory: — mesmo comportamento de
    # sempre (isolado por instancia, nao sobrevive a nada) — usado por todo
    # o resto da suite (test_session_store.py, test_api_routes.py) sem
    # precisar declarar tmp_path.
    primeira_instancia = SessionStore()
    session_id = primeira_instancia.create()

    segunda_instancia = SessionStore()
    with pytest.raises(SessionNotFound):
        segunda_instancia.get_context(session_id)
