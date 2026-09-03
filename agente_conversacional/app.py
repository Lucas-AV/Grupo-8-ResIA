import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from llm.health import check_llm_health
from spotify_auth.routes import router as spotify_auth_router

logger = logging.getLogger("agente")

_DEFAULT_FRONTEND_URL = "http://127.0.0.1:5173"


def _cors_origins():
    """Origens liberadas pro CORS (ticket 8.2) — lista separada por virgula em FRONTEND_URL."""
    origins = os.environ.get("FRONTEND_URL", _DEFAULT_FRONTEND_URL)
    return [origin.strip() for origin in origins.split(",") if origin.strip()]


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


async def handle_unhandled_exception(request: Request, exc: Exception):
    """Nunca vaza stack trace pro cliente; log completo fica so no servidor (ticket 8.3)."""
    logger.exception("erro nao tratado em %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"erro": "erro interno do servidor"})


def create_app() -> FastAPI:
    app = FastAPI(title="Agente Conversacional", lifespan=_lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(spotify_auth_router)
    app.exception_handler(Exception)(handle_unhandled_exception)

    @app.get("/health")
    def health():
        return check_llm_health()

    return app


app = create_app()
