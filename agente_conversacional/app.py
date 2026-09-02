import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

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


def create_app() -> FastAPI:
    app = FastAPI(title="Agente Conversacional", lifespan=_lifespan)

    @app.get("/health")
    def health():
        return check_llm_health()

    return app


app = create_app()
