import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import cast

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from api.routes import build_api_router
from chat.contracts import TurnProcessor
from chat.pipeline import ChatPipeline
from sessions.store import SessionStore
from llm.health import check_llm_health
from spotify_auth.explorer_routes import router as spotify_explorer_router
from spotify_auth.routes import router as spotify_auth_router

# python-dotenv ja estava no requirements.txt mas nunca era carregado —
# .env so funcionava se a variavel ja tivesse sido exportada manualmente no
# shell. Nao sobrescreve vars ja definidas no ambiente (comportamento
# padrao do dotenv, override=False). Pulado sob pytest: os testes contam
# com um ambiente limpo (mockam LLM/Spotify/etc explicitamente) e carregar
# valores reais do .env (LLM_BACKEND/OLLAMA_BASE_URL apontando pra um
# Ollama de verdade, por exemplo) quebra esse isolamento.
if "pytest" not in sys.modules:
    load_dotenv()

logger = logging.getLogger("agente")

_DEFAULT_FRONTEND_URL = "http://127.0.0.1:5173"


def _cors_origins():
    """Origens liberadas pro CORS (ticket 8.2) — lista separada por virgula em FRONTEND_URL."""
    origins = os.environ.get("FRONTEND_URL", _DEFAULT_FRONTEND_URL)
    return [origin.strip() for origin in origins.split(",") if origin.strip()]


def _default_session_db_path():
    """Caminho do SQLite pra SessionStore sobreviver a um restart do
    processo — sem isso (dict em memoria puro), todo restart derrubava
    todas as sessoes e o frontend descartava o cache local junto (parecia
    "descarregar" o chat). Pulado sob pytest: os testes usam o default
    `:memory:` de SessionStore, isolado por instancia (mesmo motivo do
    guard de load_dotenv acima — nao vale a pena arquivo real em disco
    compartilhado entre testes)."""
    if "pytest" in sys.modules:
        return None
    return os.environ.get("SESSION_DB_PATH", "sessions.db")


@asynccontextmanager
async def _lifespan(app: FastAPI):
    resultado = check_llm_health()
    if resultado["disponivel"]:
        logger.info("LLM backend '%s' disponivel no boot", resultado["backend"])
    else:
        logger.warning(
            "LLM backend '%s' indisponivel no boot: %s — API de sessões (KAN-8) "
            "continua funcionando sem LLM",
            resultado["backend"],
            resultado["erro"],
        )
    yield


async def handle_unhandled_exception(request: Request, exc: Exception):
    """Nunca vaza stack trace pro cliente; log completo fica so no servidor (ticket 8.3)."""
    logger.exception("erro nao tratado em %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"erro": "erro interno do servidor"})


def create_app(
    session_store: SessionStore | None = None,
    turn_processor: TurnProcessor | None = None,
) -> FastAPI:
    app = FastAPI(title="Agente Conversacional", lifespan=_lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.session_store = session_store or SessionStore(db_path=_default_session_db_path())
    # Épico 2: pipeline conversacional real por padrão (KAN-8 usava
    # turn_processor=None só como placeholder até este módulo existir).
    # Testes que precisam simular indisponibilidade continuam podendo
    # injetar seu próprio processor (ver test_api_routes.py).
    app.state.turn_processor = turn_processor or ChatPipeline()
    app.include_router(
        build_api_router(
            cast(SessionStore, app.state.session_store),
            cast(TurnProcessor | None, app.state.turn_processor),
        )
    )
    app.include_router(spotify_auth_router)
    app.include_router(spotify_explorer_router)
    app.exception_handler(Exception)(handle_unhandled_exception)

    @app.get("/health")
    def health():
        return check_llm_health()

    # Monta arquivos estáticos do frontend se o diretório existir
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    if os.path.isdir(frontend_dir):
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    return app


app = create_app()
