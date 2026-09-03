import logging
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI

if __package__:  # Permite ``import agente_conversacional.app``.
    from .api.routes import build_api_router
    from .chat.contracts import TurnProcessor
    from .sessions.store import SessionStore
else:  # pragma: no cover - caminho usado por ``uvicorn app:app``.
    from api.routes import build_api_router
    from chat.contracts import TurnProcessor
    from sessions.store import SessionStore

from llm.health import check_llm_health

logger = logging.getLogger("agente")


@asynccontextmanager
async def _lifespan(app: FastAPI):
    resultado = check_llm_health()
    if resultado["disponivel"]:
        logger.info("LLM backend '%s' disponivel no boot", resultado["backend"])
    else:
        logger.warning(
            "LLM backend '%s' indisponivel no boot: %s — roteador determinístico "
            "continua funcionando sem LLM",
            resultado["backend"],
            resultado["erro"],
        )
    yield


def create_app(
    session_store: SessionStore | None = None,
    turn_processor: TurnProcessor | None = None,
) -> FastAPI:
    app = FastAPI(title="Agente Conversacional", lifespan=_lifespan)
    app.state.session_store = session_store or SessionStore()
    app.state.turn_processor = turn_processor
    app.include_router(
        build_api_router(
            cast(SessionStore, app.state.session_store),
            cast(TurnProcessor | None, app.state.turn_processor),
        )
    )

    @app.get("/health")
    def health():
        return check_llm_health()

    return app


app = create_app()
