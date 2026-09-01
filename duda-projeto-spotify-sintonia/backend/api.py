"""API HTTP mínima para a integração Spotify acadêmica."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from backend.configuracao.ambiente import Configuracao
from backend.integracoes.spotify import (
    ArmazenamentoSessoesSpotify,
    ClienteSpotifyDemo,
    ClienteSpotifyReal,
    ColetaSpotify,
    ErroSpotify,
)
from backend.integracoes.spotify.modelos import PerfilSpotify

NOME_COOKIE_SESSAO = "spotify_insights_sessao"
Periodo = Literal["short_term", "medium_term", "long_term"]


@dataclass
class ContextoSpotify:
    configuracao: Configuracao
    sessoes: ArmazenamentoSessoesSpotify
    cliente_real: ClienteSpotifyReal
    cliente_demo: ClienteSpotifyDemo

    @classmethod
    def criar(cls, configuracao: Configuracao | None = None) -> ContextoSpotify:
        configuracao_final = configuracao or Configuracao()
        return cls(
            configuracao=configuracao_final,
            sessoes=ArmazenamentoSessoesSpotify(),
            cliente_real=ClienteSpotifyReal(configuracao_final),
            cliente_demo=ClienteSpotifyDemo(),
        )


def criar_aplicacao(contexto: ContextoSpotify | None = None) -> FastAPI:
    contexto_final = contexto or ContextoSpotify.criar()
    configuracao = contexto_final.configuracao
    app = FastAPI(title="Spotify Insights API", version="0.1.0")
    app.state.contexto_spotify = contexto_final
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[configuracao.spotify_url_frontend],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.exception_handler(ErroSpotify)
    async def tratar_erro_spotify(_: Request, erro: ErroSpotify) -> Response:
        cabecalhos = {"Retry-After": str(erro.retry_after)} if erro.retry_after is not None else None
        return JSONResponse(
            content={"erro": erro.codigo, "mensagem": erro.mensagem},
            status_code=erro.status_http,
            headers=cabecalhos,
        )

    @app.get("/status")
    def status() -> dict[str, str]:
        return {"status": "ok", "modo_spotify": configuracao.spotify_modo}

    @app.get("/auth/spotify/iniciar")
    def iniciar_login() -> RedirectResponse:
        if _modo_demo(configuracao):
            return RedirectResponse(f"{configuracao.spotify_url_frontend}?spotify=demo")
        identificador, estado = contexto_final.sessoes.criar()
        resposta = RedirectResponse(contexto_final.cliente_real.url_autorizacao(estado))
        resposta.set_cookie(
            NOME_COOKIE_SESSAO,
            identificador,
            httponly=True,
            secure=configuracao.spotify_cookie_secure,
            samesite="lax",
            max_age=2 * 60 * 60,
        )
        return resposta

    @app.get("/auth/spotify/callback")
    def concluir_login(request: Request, code: str | None = None, state: str | None = None, error: str | None = None) -> RedirectResponse:
        if error:
            raise HTTPException(status_code=400, detail="A autorização Spotify foi cancelada ou recusada.")
        identificador = request.cookies.get(NOME_COOKIE_SESSAO)
        sessao = contexto_final.sessoes.obter(identificador)
        if not code or not state or sessao is None or state != sessao.estado:
            raise HTTPException(status_code=400, detail="Não foi possível validar o retorno do Spotify.")
        contexto_final.sessoes.salvar_token(identificador, contexto_final.cliente_real.trocar_codigo(code))
        return RedirectResponse(f"{configuracao.spotify_url_frontend}?spotify=conectado")

    @app.post("/auth/spotify/sair", status_code=204)
    def sair(request: Request, response: Response) -> None:
        contexto_final.sessoes.remover(request.cookies.get(NOME_COOKIE_SESSAO))
        response.delete_cookie(NOME_COOKIE_SESSAO)

    @app.get("/api/spotify/usuarios-demo")
    def usuarios_demo() -> dict[str, list[str]]:
        return {"usuarios": contexto_final.cliente_demo.listar_usuarios()}

    @app.get("/api/spotify/perfil", response_model=PerfilSpotify)
    def perfil(request: Request, usuario_demo: str = "ecletico") -> PerfilSpotify:
        return _coletar(contexto_final, request, "medium_term", 1, usuario_demo).perfil

    @app.get("/api/spotify/top-faixas", response_model=ColetaSpotify)
    def top_faixas(
        request: Request,
        periodo: Periodo = "medium_term",
        limite: int = Query(default=20, ge=1, le=50),
        usuario_demo: str = "ecletico",
    ) -> ColetaSpotify:
        return _coletar(contexto_final, request, periodo, limite, usuario_demo)

    @app.get("/api/spotify/top-artistas", response_model=ColetaSpotify)
    def top_artistas(
        request: Request,
        periodo: Periodo = "medium_term",
        limite: int = Query(default=20, ge=1, le=50),
        usuario_demo: str = "ecletico",
    ) -> ColetaSpotify:
        return _coletar(contexto_final, request, periodo, limite, usuario_demo)

    return app


def _modo_demo(configuracao: Configuracao) -> bool:
    if configuracao.spotify_modo not in {"demo", "real"}:
        raise ErroSpotify("SPOTIFY_MODO deve ser 'demo' ou 'real'.", status_http=500, codigo="spotify_modo_invalido")
    return configuracao.spotify_modo == "demo"


def _coletar(contexto: ContextoSpotify, request: Request, periodo: Periodo, limite: int, usuario_demo: str) -> ColetaSpotify:
    if _modo_demo(contexto.configuracao):
        try:
            return contexto.cliente_demo.coletar(usuario_demo, periodo, limite)
        except ValueError as erro:
            raise HTTPException(status_code=404, detail=str(erro)) from erro
    identificador = request.cookies.get(NOME_COOKIE_SESSAO)
    sessao = contexto.sessoes.obter(identificador)
    if sessao is None or sessao.token_info is None:
        raise ErroSpotify("Conecte sua conta Spotify antes de coletar seus dados.", status_http=401, codigo="spotify_nao_conectado")
    token = contexto.cliente_real.renovar_se_necessario(sessao.token_info)
    contexto.sessoes.salvar_token(identificador, token)
    return contexto.cliente_real.coletar(token, periodo, limite)


app = criar_aplicacao()
