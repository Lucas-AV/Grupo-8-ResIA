"""Rotas do KAN-8, isoladas do bootstrap da aplicação."""

import logging

from fastapi import APIRouter, HTTPException, status

from api.schemas import (
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    HistoryMessage,
    SessionResponse,
    TrackItem,
)
from chat.contracts import PipelineUnavailableError, TurnProcessor
from sessions.store import SessionNotFound, SessionStore

logger = logging.getLogger("agente.api")


def build_api_router(
    session_store: SessionStore,
    turn_processor: TurnProcessor | None = None,
) -> APIRouter:
    router = APIRouter()

    @router.post("/session", response_model=SessionResponse)
    def criar_sessao() -> SessionResponse:
        return SessionResponse(session_id=session_store.create())

    @router.get("/chat/historico", response_model=ChatHistoryResponse)
    def obter_historico(session_id: str) -> ChatHistoryResponse:
        try:
            history = session_store.get_history(session_id)
        except SessionNotFound:
            _raise_invalid_session()
        return ChatHistoryResponse(
            session_id=session_id,
            historico=[
                HistoryMessage(
                    role=message.role,
                    conteudo=message.conteudo,
                    faixas_citadas=list(message.faixas_citadas),
                    timestamp=message.timestamp,
                )
                for message in history
            ],
        )

    @router.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> ChatResponse:
        try:
            context = session_store.get_context(request.session_id)
        except SessionNotFound:
            _raise_invalid_session()

        if turn_processor is None:
            _raise_pipeline_unavailable()

        try:
            result = turn_processor.process(request.mensagem, context)
            session_store.commit_turn(request.session_id, request.mensagem, result)
        except SessionNotFound:
            _raise_invalid_session()
        except PipelineUnavailableError:
            _raise_pipeline_unavailable()

        return ChatResponse(
            session_id=request.session_id,
            mensagem=result.mensagem,
            faixas=[
                TrackItem(
                    track_id=track.track_id,
                    nome=track.nome,
                    artista=track.artista,
                    album=track.album,
                    genero=track.genero,
                )
                for track in result.faixas
            ],
            diversidade_generos=result.diversidade_generos,
            cobertura_sessao=result.cobertura_sessao,
            consulta_efetiva=dict(result.consulta_efetiva),
        )

    return router


def _raise_invalid_session() -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "codigo": "sessao_invalida",
            "mensagem": "Sessão inexistente ou expirada.",
        },
    )


def _raise_pipeline_unavailable() -> None:
    logger.info("pipeline conversacional indisponível para o turno")
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "codigo": "pipeline_indisponivel",
            "mensagem": "O pipeline conversacional ainda não está disponível.",
        },
    )
