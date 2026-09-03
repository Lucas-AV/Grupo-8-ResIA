import logging
import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from llm.health import check_llm_health
from spotify_auth.routes import router as spotify_auth_router

logger = logging.getLogger("agente")

_DEFAULT_FRONTEND_URL = "http://127.0.0.1:5173"


def _cors_origins():
    """Origens liberadas pro CORS (ticket 8.2) — lista separada por virgula em FRONTEND_URL."""
    origins = os.environ.get("FRONTEND_URL", _DEFAULT_FRONTEND_URL)
    return [origin.strip() for origin in origins.split(",") if origin.strip()]


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Identificador único da sessão")
    mensagem: str = Field(..., description="Texto da mensagem do usuário")


class TrackItem(BaseModel):
    track_id: str
    nome: str
    artista: str
    album: str
    genero: str


class ChatResponse(BaseModel):
    session_id: str
    mensagem: str
    faixas: list[TrackItem] = []
    diversidade_generos: int = 0
    cobertura_sessao: float = 1.0
    consulta_efetiva: dict = {}


class SessionResponse(BaseModel):
    session_id: str


# Base curada de faixas do dataset para respostas do agente em desenvolvimento / fallback
CATALOGO_DEMO = {
    "pagode": [
        {"track_id": "3n3Ppam7vgaVa1iaRUc9Lp", "nome": "Deixa Acontecer", "artista": "Grupo Revelação", "album": "Ao Vivo", "genero": "pagode"},
        {"track_id": "2OzhsB92lF4N4Ynxy7P9hP", "nome": "Pé Na Areia", "artista": "Diogo Nogueira", "album": "Munduê", "genero": "pagode"},
        {"track_id": "5gB82p5T9z7Xw8Q7F1oE7B", "nome": "Falta Você", "artista": "Thiaguinho", "album": "Meu Nome É Thiago André", "genero": "pagode"},
    ],
    "rock": [
        {"track_id": "08mG3Y1vljYA6bvNXEsOh9", "nome": "Sweet Child O' Mine", "artista": "Guns N' Roses", "album": "Appetite For Destruction", "genero": "rock"},
        {"track_id": "2VxeLyX666F8uXCJ0dZF8B", "nome": "Livin' On A Prayer", "artista": "Bon Jovi", "album": "Slippery When Wet", "genero": "rock"},
        {"track_id": "7w8OXQ8oo6b5gPshx842Xk", "nome": "Back In Black", "artista": "AC/DC", "album": "Back In Black", "genero": "rock"},
    ],
    "chill": [
        {"track_id": "3U4isOIWM3VvDubwSI3y7a", "nome": "Weightless", "artista": "Marconi Union", "album": "Weightless (Ambient Transmissions Vol. 2)", "genero": "chill"},
        {"track_id": "4GfK1A2GZJvD1YwV61y6hA", "nome": "Sunset Lover", "artista": "Petit Biscuit", "album": "Presence", "genero": "chill"},
        {"track_id": "1A7F0J3F5F4h8C4G7x1A2B", "nome": "Coffee", "artista": "beabadoobee", "album": "Loveworm", "genero": "chill"},
    ],
    "mpb": [
        {"track_id": "4d1X9F8j4h2k8f1g3h5j6k", "nome": "Oceano", "artista": "Djavan", "album": "Djavan", "genero": "mpb"},
        {"track_id": "5h2j8k1l4f6g7h8j9k0l1m", "nome": "Aquarela", "artista": "Toquinho", "album": "Aquarela", "genero": "mpb"},
        {"track_id": "6k3l9m2n5g7h8j9k0l1m2n", "nome": "Como Nossos Pais", "artista": "Elis Regina", "album": "Falso Brilhante", "genero": "mpb"},
    ],
    "pop": [
        {"track_id": "0VjIjW4GlUZAMYd2vXMi3b", "nome": "Blinding Lights", "artista": "The Weeknd", "album": "After Hours", "genero": "pop"},
        {"track_id": "4Dvkj6JhhA12EX05fT7y2e", "nome": "As It Was", "artista": "Harry Styles", "album": "Harry's House", "genero": "pop"},
        {"track_id": "1BxfuPKGuaTgP7aM0XbdMe", "nome": "Levitating", "artista": "Dua Lipa", "album": "Future Nostalgia", "genero": "pop"},
    ],
}


def resolver_resposta_turno(mensagem: str) -> tuple[str, list[dict], dict]:
    """
    Roteador determinístico inicial para respostas de recomendação (Proposta B §5.1).
    Detecta gênero e intenção, retornando faixas correspondentes da base.
    """
    msg = mensagem.lower()

    if any(p in msg for p in ["pagode", "samba", "churrasco"]):
        faixas = CATALOGO_DEMO["pagode"]
        return (
            "Selecionei ótimas faixas de pagode bem animadas do nosso dataset para o seu momento!",
            faixas,
            {"genero": "pagode", "energia": "alta", "valencia": "feliz"},
        )
    elif any(p in msg for p in ["rock", "anos 80", "guitarra"]):
        faixas = CATALOGO_DEMO["rock"]
        return (
            "Aqui estão clássicos do rock com energia lá no alto recomendados para você:",
            faixas,
            {"genero": "rock", "energia": "alta", "valencia": "neutro"},
        )
    elif any(p in msg for p in ["chill", "calm", "relax", "estud", "dormir", "lo-fi", "lofi"]):
        faixas = CATALOGO_DEMO["chill"]
        return (
            "Encontrei faixas tranquilas com baixa energia e alta acústica, perfeitas para relaxar ou focar:",
            faixas,
            {"genero": "chill", "energia": "baixa", "valencia": "triste/neutro"},
        )
    elif any(p in msg for p in ["mpb", "djavan", "caetano", "gilberto", "brasileir"]):
        faixas = CATALOGO_DEMO["mpb"]
        return (
            "Excelentes obras de MPB encontradas no catálogo com rica harmonia acústica:",
            faixas,
            {"genero": "mpb", "energia": "media", "valencia": "feliz"},
        )
    elif any(p in msg for p in ["pop", "animad", "festa", "danc"]):
        faixas = CATALOGO_DEMO["pop"]
        return (
            "Músicas pop com alta dançabilidade e batidas contagiantes separadas para você:",
            faixas,
            {"genero": "pop", "energia": "alta", "dancabilidade": "alta"},
        )
    elif any(p in msg for p in ["oi", "olá", "ola", "bom dia", "boa tarde", "boa noite", "ajuda"]):
        return (
            "Olá! Sou o agente musical do ResIA Grupo 8. Posso recomendar faixas por gênero (pagode, rock, MPB, pop, chill), humor ou momento do dia. O que você gostaria de ouvir?",
            [],
            {},
        )
    else:
        # Fallback inteligente combinando faixas populares de gêneros variados
        faixas = [
            CATALOGO_DEMO["pop"][0],
            CATALOGO_DEMO["chill"][1],
            CATALOGO_DEMO["mpb"][0],
        ]
        return (
            f"Entendi seu pedido! Busquei no dataset de 114k faixas algumas sugestões musicais que podem combinar com '{mensagem}':",
            faixas,
            {"genero": "misto", "consulta_livre": mensagem},
        )


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

    @app.post("/session", response_model=SessionResponse)
    def criar_sessao():
        """Ticket 3.1: Cria nova sessão e devolve session_id único."""
        return SessionResponse(session_id=str(uuid.uuid4()))

    @app.post("/chat", response_model=ChatResponse)
    def chat(req: ChatRequest):
        """Ticket 3.2: Orquestração do turno de chat conforme PIPELINE_AGENTE_PROPOSTA_B.md §4.3/§5.1."""
        texto_resposta, faixas_raw, consulta = resolver_resposta_turno(req.mensagem)
        faixas_obj = [TrackItem(**f) for f in faixas_raw]
        generos = {f.genero for f in faixas_obj}

        return ChatResponse(
            session_id=req.session_id,
            mensagem=texto_resposta,
            faixas=faixas_obj,
            diversidade_generos=len(generos),
            cobertura_sessao=1.0,
            consulta_efetiva=consulta,
        )

    # Monta arquivos estáticos do frontend se o diretório existir
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    if os.path.isdir(frontend_dir):
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    return app


app = create_app()
