import logging
import time
import uuid
from typing import Optional

import segno
from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

from api.schemas import TrackItem
from chat.playlist_sugestao import sugerir_titulo_descricao
from spotify_auth.client import PendingAuth, build_authorize_url, exchange_code_for_tokens, get_valid_access_token
from spotify_auth.consent import render_consent_page
from spotify_auth.errors import SpotifyNotAuthenticatedError, SpotifyPlaylistError, SpotifyTokenExchangeError
from spotify_auth.pairing_store import PairingStore
from spotify_auth.playlist import create_playlist_with_tracks
from spotify_auth.token_store import TokenStore
from spotify_auth.history import fetch_recently_played, fetch_saved_tracks, fetch_top_tracks
from recomendacao.historico_match import casar_historico_com_dataset
from recomendacao.perfil import calcular_perfil_usuario
from sessions.store import SessionNotFound

logger = logging.getLogger("agente.spotify_auth")

router = APIRouter()
_pending_auth = PendingAuth()
_pairing_store = PairingStore()
_token_store = None

# Ticket KAN-QR (abrir o Spotify no celular): deep link do app + link universal.
# `spotify:` é o esquema de URI que o app registra nos dois sistemas (é o mesmo
# prefixo dos `uri` que a Web API devolve) e é o caminho que funciona dentro de
# navegadores embutidos (Instagram/TikTok), onde universal link não dispara.
# `https://open.spotify.com/` é universal link no iOS e App Link no Android:
# abre o app quando instalado e, quando não está, cai no player web em vez de
# deixar a pessoa numa tela de erro. Por isso a página usa os dois, nessa ordem.
_SPOTIFY_APP_URI = "spotify://open.spotify.com/"
_SPOTIFY_WEB_URL = "https://open.spotify.com/"

_SPOTIFY_GLYPH = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.485 17.307'
    "c-.215.353-.675.466-1.027.25-2.813-1.718-6.353-2.107-10.523-1.155-.403.092-.806-.16-.898-.564"
    "-.092-.403.16-.806.564-.898 4.566-1.042 8.487-.6 11.634 1.34.352.216.465.675.25 1.027zm1.464-3.26"
    "c-.27.44-.847.58-1.288.31-3.22-1.98-8.127-2.55-11.936-1.393-.497.15-1.028-.135-1.18-.63-.15-.497"
    ".135-1.028.63-1.18 4.354-1.32 9.774-.688 13.464 1.584.44.27.58.847.31 1.288zm.126-3.41"
    "c-3.86-2.29-10.224-2.5-13.882-1.39-.59.18-1.22-.16-1.4-.75-.18-.59.16-1.22.75-1.4 4.21-1.28 "
    '11.23-1.04 15.68 1.6.53.31.7.99.39 1.52-.31.53-.99.7-1.52.39z"/></svg>'
)

# CSS inline de propósito: essa página é servida solta pelo FastAPI no celular
# de quem escaneou o QR, sem acesso ao frontend/style.css nem a CDN nenhuma
# (a demo roda em rede local). Tokens copiados do design system (Ticket 4.1).
_PAIRING_PAGE_STYLE = """
    :root {
      --bg-base: #0b0b0b;
      --bg-card: rgba(21, 21, 21, 0.9);
      --spotify-green: #1db954;
      --spotify-green-hover: #1ed760;
      --text-primary: #ffffff;
      --text-secondary: #b8b8b8;
      --text-muted: #a0a0a0;
      --border-subtle: rgba(255, 255, 255, 0.09);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html { -webkit-text-size-adjust: 100%; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI Variable Display",
        "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
      background-color: var(--bg-base);
      background-image:
        radial-gradient(circle at 50% -10%, rgba(29, 185, 84, 0.22), transparent 55%),
        radial-gradient(circle at 12% 108%, rgba(16, 185, 129, 0.12), transparent 45%);
      background-attachment: fixed;
      color: var(--text-primary);
      min-height: 100vh;
      min-height: 100dvh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 28px 18px calc(28px + env(safe-area-inset-bottom));
      line-height: 1.5;
    }
    .card {
      width: 100%;
      max-width: 400px;
      background: var(--bg-card);
      -webkit-backdrop-filter: blur(18px);
      backdrop-filter: blur(18px);
      border: 1px solid var(--border-subtle);
      border-radius: 28px;
      padding: 34px 26px 24px;
      text-align: center;
      box-shadow: 0 24px 60px rgba(0, 0, 0, 0.65), 0 0 44px rgba(29, 185, 84, 0.08);
      animation: rise 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
    }
    .seal {
      position: relative;
      width: 84px;
      height: 84px;
      margin: 0 auto 20px;
    }
    .seal::after {
      content: "";
      position: absolute;
      inset: -14px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(29, 185, 84, 0.28), transparent 68%);
      animation: pulse 2.6s ease-in-out infinite;
    }
    .seal svg { position: relative; width: 100%; height: 100%; display: block; }
    .seal circle, .seal path {
      fill: none;
      stroke: var(--spotify-green);
      stroke-width: 3.5;
      stroke-linecap: round;
      stroke-linejoin: round;
    }
    .seal circle {
      stroke-dasharray: 226;
      stroke-dashoffset: 226;
      animation: draw 0.75s cubic-bezier(0.65, 0, 0.35, 1) 0.12s forwards;
    }
    .seal path {
      stroke-width: 4.5;
      stroke-dasharray: 48;
      stroke-dashoffset: 48;
      animation: draw 0.35s cubic-bezier(0.65, 0, 0.35, 1) 0.68s forwards;
    }
    .eyebrow {
      display: inline-block;
      font-size: 0.66rem;
      font-weight: 700;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      color: var(--spotify-green);
      background: rgba(29, 185, 84, 0.12);
      border: 1px solid rgba(29, 185, 84, 0.28);
      border-radius: 9999px;
      padding: 5px 12px;
      margin-bottom: 14px;
      animation: rise 0.5s cubic-bezier(0.16, 1, 0.3, 1) 0.2s both;
    }
    h1 {
      font-size: 1.6rem;
      font-weight: 800;
      letter-spacing: -0.025em;
      margin-bottom: 10px;
      animation: rise 0.5s cubic-bezier(0.16, 1, 0.3, 1) 0.26s both;
    }
    .lead {
      color: var(--text-secondary);
      font-size: 0.94rem;
      margin-bottom: 20px;
      animation: rise 0.5s cubic-bezier(0.16, 1, 0.3, 1) 0.32s both;
    }
    .handoff {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      text-align: left;
      background: rgba(29, 185, 84, 0.07);
      border-left: 3px solid var(--spotify-green);
      border-radius: 8px;
      padding: 11px 13px;
      margin-bottom: 22px;
      font-size: 0.82rem;
      color: var(--text-secondary);
      animation: rise 0.5s cubic-bezier(0.16, 1, 0.3, 1) 0.38s both;
    }
    .handoff strong { color: var(--text-primary); font-weight: 600; }
    .handoff span[aria-hidden] { font-size: 1rem; line-height: 1.3; }
    .btn {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      width: 100%;
      padding: 15px 22px;
      border-radius: 9999px;
      background: var(--spotify-green);
      color: #000000;
      font-size: 1rem;
      font-weight: 700;
      text-decoration: none;
      box-shadow: 0 6px 20px rgba(29, 185, 84, 0.3);
      transition: background-color 0.2s, transform 0.15s;
      animation: rise 0.5s cubic-bezier(0.16, 1, 0.3, 1) 0.44s both;
    }
    .btn:active { transform: scale(0.98); background: var(--spotify-green-hover); }
    .btn svg { width: 21px; height: 21px; fill: currentColor; flex-shrink: 0; }
    .fallback {
      display: inline-block;
      margin-top: 14px;
      color: var(--text-muted);
      font-size: 0.81rem;
      text-decoration: underline;
      text-underline-offset: 3px;
      animation: rise 0.5s cubic-bezier(0.16, 1, 0.3, 1) 0.5s both;
    }
    footer {
      margin-top: 22px;
      padding-top: 16px;
      border-top: 1px solid var(--border-subtle);
      font-size: 0.68rem;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: #7c7c7c;
    }
    @keyframes rise { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }
    @keyframes draw { to { stroke-dashoffset: 0; } }
    @keyframes pulse { 0%, 100% { opacity: 0.55; transform: scale(0.94); } 50% { opacity: 1; transform: scale(1.06); } }
    @media (prefers-reduced-motion: reduce) {
      *, *::after { animation: none !important; transition: none !important; }
      .seal circle, .seal path { stroke-dashoffset: 0; }
    }
"""

_PAIRING_SUCCESS_PAGE = (
    """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="color-scheme" content="dark">
  <title>Spotify conectado — SyntonIA</title>
  <style>__STYLE__</style>
</head>
<body>
  <main class="card">
    <div class="seal">
      <svg viewBox="0 0 84 84" aria-hidden="true" focusable="false">
        <circle cx="42" cy="42" r="36"></circle>
        <path d="M27 43.5 L37.5 54 L57 32"></path>
      </svg>
    </div>
    <p class="eyebrow">Pareamento concluído</p>
    <h1>Spotify conectado!</h1>
    <p class="lead">Sua conta já foi entregue pro outro dispositivo — não precisa fazer mais nada por aqui.</p>
    <p class="handoff">
      <span aria-hidden="true">📺</span>
      <span><strong>Pode voltar pro outro dispositivo</strong> e fechar essa aba. O login continua valendo lá mesmo se você sair daqui.</span>
    </p>
    <a class="btn" id="abrir-spotify" href="__WEB_URL__" data-app-uri="__APP_URI__">
      __GLYPH__
      <span>Abrir o Spotify</span>
    </a>
    <a class="fallback" href="__WEB_URL__">Não abriu? Usar o player no navegador</a>
    <footer>SyntonIA · Grupo 8 ResIA</footer>
  </main>
  <script>
  (function () {
    var APP_URI = '__APP_URI__';
    var WEB_URL = '__WEB_URL__';
    var botao = document.getElementById('abrir-spotify');
    var saiuDaPagina = false;

    // Se o app abriu, o navegador vira background: para de tentar o fallback.
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) { saiuDaPagina = true; }
    });
    window.addEventListener('pagehide', function () { saiuDaPagina = true; });

    // Tentativa automática, silenciosa: iframe com o esquema do app nunca
    // mostra tela de erro quando o Spotify não está instalado (o navegador
    // simplesmente ignora). iOS/Chrome modernos bloqueiam esse atalho — por
    // isso ela é só um bônus, o caminho confiável é o botão abaixo, que roda
    // dentro de um gesto real do usuário (exigência do Safari no iOS).
    setTimeout(function () {
      if (saiuDaPagina) { return; }
      var quadro = document.createElement('iframe');
      quadro.setAttribute('aria-hidden', 'true');
      quadro.style.display = 'none';
      quadro.src = APP_URI;
      document.body.appendChild(quadro);
      setTimeout(function () { quadro.parentNode && quadro.parentNode.removeChild(quadro); }, 1500);
    }, 600);

    if (botao) {
      botao.addEventListener('click', function (evento) {
        evento.preventDefault();
        saiuDaPagina = false;
        window.location.href = APP_URI;
        // App não instalado / esquema bloqueado: continuamos visíveis, então
        // seguimos pro link universal (abre o app no iOS/Android e, sem app,
        // o player web) em vez de deixar a pessoa achando que travou.
        setTimeout(function () {
          if (!saiuDaPagina && !document.hidden) { window.location.href = WEB_URL; }
        }, 1200);
      });
    }
  })();
  </script>
</body>
</html>"""
    .replace("__STYLE__", _PAIRING_PAGE_STYLE)
    .replace("__GLYPH__", _SPOTIFY_GLYPH)
    .replace("__APP_URI__", _SPOTIFY_APP_URI)
    .replace("__WEB_URL__", _SPOTIFY_WEB_URL)
)

_PAIRING_EXPIRED_PAGE = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="color-scheme" content="dark">
  <title>QR code expirado — SyntonIA</title>
  <style>__STYLE__
    .seal circle, .seal path { stroke: #f15e5e; }
    .seal::after { background: radial-gradient(circle, rgba(241, 94, 94, 0.24), transparent 68%); }
    .eyebrow { color: #f15e5e; background: rgba(241, 94, 94, 0.12); border-color: rgba(241, 94, 94, 0.28); }
    .handoff { background: rgba(241, 94, 94, 0.07); border-left-color: #f15e5e; }
  </style>
</head>
<body>
  <main class="card">
    <div class="seal">
      <svg viewBox="0 0 84 84" aria-hidden="true" focusable="false">
        <circle cx="42" cy="42" r="36"></circle>
        <path d="M42 26 L42 46 M42 56 L42 56.5"></path>
      </svg>
    </div>
    <p class="eyebrow">Pareamento não concluído</p>
    <h1>Esse QR code expirou</h1>
    <p class="lead">Cada QR code vale por poucos minutos, por segurança. Nenhum dado da sua conta foi guardado.</p>
    <p class="handoff">
      <span aria-hidden="true">📺</span>
      <span><strong>Volte pro outro dispositivo</strong> e gere um novo QR code pra escanear de novo.</span>
    </p>
    <footer>SyntonIA · Grupo 8 ResIA</footer>
  </main>
</body>
</html>""".replace("__STYLE__", _PAIRING_PAGE_STYLE)


class CriarPlaylistRequest(BaseModel):
    """Corpo do POST /playlist/criar (ticket 12.1)."""

    session_id: str = Field(min_length=1)
    faixas: list[str] = Field(min_length=1, description="track_ids do Spotify a adicionar na playlist")
    nome: Optional[str] = None
    descricao: Optional[str] = None


class SugerirPlaylistRequest(BaseModel):
    """Corpo do POST /playlist/sugerir (ticket 12.6)."""

    faixas: list[TrackItem] = Field(min_length=1)


def _get_token_store():
    global _token_store
    if _token_store is None:
        _token_store = TokenStore()
    return _token_store


def _perfil_e_cobertura_do_historico(access_token):
    """Calcula o perfil e registra somente números agregados do matching.

    O log não contém token, sessão, nomes de faixas nem informações da conta.
    Falhas aqui nunca impedem a pessoa de concluir o login.
    """
    try:
        historico = [
            *fetch_top_tracks(access_token),
            *fetch_recently_played(access_token),
            *fetch_saved_tracks(access_token),
        ]
        cobertura = casar_historico_com_dataset(historico)
        perfil = calcular_perfil_usuario(historico)
        logger.info(
            "cobertura_matching_oauth=%.1f%% faixas_casadas=%d faixas_historico=%d",
            cobertura["taxa_cobertura"] * 100,
            cobertura["total_casadas"],
            cobertura["total_historico"],
        )
        return perfil
    except Exception:
        logger.warning("não foi possível calcular a cobertura do matching OAuth; seguindo sem perfil", exc_info=True)
        return None


@router.get("/auth/login")
def login(session_id: str = Query(...)):
    """Aviso de consentimento (ticket 5.10) antes do redirect real pro Spotify."""
    return HTMLResponse(render_consent_page(session_id))


@router.get("/auth/login/start")
def login_start(session_id: str = Query(...), pair: Optional[str] = Query(None)):
    """`pair` (opcional, ticket 13.13): quando presente, veio de um QR code de
    pareamento — o callback vai relayar os tokens pro código em vez de (só)
    salvar na sessão que de fato completou o OAuth (ver `/auth/qr`)."""
    return RedirectResponse(build_authorize_url(session_id, _pending_auth, pair_code=pair))


@router.get("/auth/callback")
def callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    if error:
        logger.info("login Spotify cancelado pelo usuario (%s) — sessao permanece anonima", error)
        return RedirectResponse("/?spotify_login=cancelled")

    pending = _pending_auth.consume(state) if state else None
    if pending is None:
        logger.warning("callback do Spotify com 'state' invalido ou desconhecido (possivel CSRF)")
        return RedirectResponse("/?spotify_login=state_mismatch")

    try:
        tokens = exchange_code_for_tokens(code, pending["code_verifier"])
    except SpotifyTokenExchangeError as exc:
        logger.warning("falha ao trocar codigo por token: %s", exc)
        return RedirectResponse("/?spotify_login=failed")

    pair_code = pending.get("pair_code")
    if pair_code:
        # Ticket 13.13: quem completou o OAuth foi o celular que escaneou o QR —
        # essa sessao (`pending["session_id"]`) e descartavel, os tokens de
        # verdade vao pro relay efemero pra o dispositivo que gerou o QR
        # (kiosk) consumir via /auth/pair/{code}/status.
        relayed = _pairing_store.mark_completed(pair_code, dict(tokens))
        if not relayed:
            logger.info("codigo de pareamento '%s' expirou antes do OAuth terminar", pair_code)
            return HTMLResponse(_PAIRING_EXPIRED_PAGE, status_code=410)
        return HTMLResponse(_PAIRING_SUCCESS_PAGE)

    expires_at = time.time() + tokens["expires_in"]
    _get_token_store().save(pending["session_id"], tokens["access_token"], tokens["refresh_token"], expires_at)
    session_store = getattr(request.app.state, "session_store", None)
    if session_store is not None:
        try:
            session_store.mark_authenticated(
                pending["session_id"],
                _perfil_e_cobertura_do_historico(tokens["access_token"]),
            )
        except SessionNotFound:
            logger.info("sessao de chat nao existe mais; tokens OAuth permanecem armazenados")
    return RedirectResponse("/?spotify_login=success")


@router.post("/auth/logout")
def logout(session_id: str = Query(...)):
    _get_token_store().delete(session_id)
    return {"status": "logged_out"}


@router.get("/auth/status")
def auth_status(session_id: str = Query(...)):
    """Ticket 12.2: o frontend usa isso pra saber se mostra acoes que exigem
    login com o Spotify (ex.: botao "Salvar no Spotify") sem precisar
    depender so do parametro `spotify_login` do redirect do callback."""
    return {"autenticado": _get_token_store().get(session_id) is not None}


@router.get("/auth/qr")
def auth_qr(request: Request, session_id: str = Query(...)):
    """Ticket 13.13: gera um QR code de pareamento — o dispositivo que chama
    essa rota (kiosk) mostra o QR, outro dispositivo (celular) escaneia,
    autoriza a própria conta Spotify, e o kiosk recebe os tokens via polling
    em `/auth/pair/{code}/status`. Porta `spotify_explorer/app.py` (`/login/qr`
    + `pairing_store.py`) — nunca implementar esse fluxo em
    `spotify_explorer/frontend/`, aquilo é a ferramenta de dev."""
    code = _pairing_store.create()
    phone_session_id = f"qr-pair-{uuid.uuid4().hex}"
    pair_login_url = str(
        request.url_for("login_start").include_query_params(session_id=phone_session_id, pair=code)
    )
    qr_svg_data_uri = segno.make(pair_login_url).svg_data_uri(scale=6)
    return {
        "code": code,
        "qr_svg_data_uri": qr_svg_data_uri,
        "pair_login_url": pair_login_url,
        "expira_em_segundos": 300,
    }


@router.get("/auth/pair/{code}/status")
def auth_pair_status(code: str, request: Request, session_id: str = Query(...)):
    """Ticket 13.13: o kiosk faz polling nessa rota até `status == "completed"` —
    nesse ponto os tokens já foram salvos na sessão do kiosk (`session_id`,
    a mesma passada em `/auth/qr`), igual a um login normal via `/auth/callback`."""
    status_str, tokens = _pairing_store.consume_if_completed(code)
    if status_str == "completed":
        expires_at = time.time() + tokens["expires_in"]
        _get_token_store().save(session_id, tokens["access_token"], tokens["refresh_token"], expires_at)
        session_store = getattr(request.app.state, "session_store", None)
        if session_store is not None:
            try:
                session_store.mark_authenticated(session_id)
            except SessionNotFound:
                logger.info("sessao de chat nao existe mais; tokens OAuth permanecem armazenados")
    return {"status": status_str}


@router.post("/playlist/criar")
def criar_playlist(body: CriarPlaylistRequest):
    """Ticket 12.1 (KAN-104): cria uma playlist de verdade na conta Spotify
    da sessao autenticada com as faixas recomendadas, usando o access_token
    valido de spotify_auth/client.py (ticket 5.4, renova sozinho quando
    necessario). Sessao sem login no Spotify nunca chega a tentar criar
    playlist nenhuma — falha cedo com 401 e um codigo de erro claro."""
    try:
        access_token = get_valid_access_token(body.session_id, _get_token_store())
    except SpotifyNotAuthenticatedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "codigo": "spotify_nao_autenticado",
                "mensagem": "Faça login com o Spotify antes de salvar uma playlist.",
            },
        )

    try:
        resultado = create_playlist_with_tracks(access_token, body.faixas, nome=body.nome, descricao=body.descricao)
    except SpotifyPlaylistError as exc:
        logger.warning("falha ao criar playlist no Spotify: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "codigo": "spotify_playlist_falhou",
                "mensagem": "Não foi possível criar a playlist no Spotify agora. Tente novamente em instantes.",
            },
        )

    return resultado


@router.post("/playlist/sugerir")
def sugerir_playlist(body: SugerirPlaylistRequest) -> dict:
    """Ticket 12.6: sugere título/descrição pra playlist via LLM, a partir
    das faixas que serão salvas — usado pelo modal de confirmação antes de
    POST /playlist/criar. Só gera texto (não fala com a Spotify), então não
    exige sessão autenticada como o /playlist/criar exige. Nunca falha: em
    qualquer problema com o LLM, `sugerir_titulo_descricao` já degrada pro
    nome/descrição padrão sozinha."""
    faixas = [faixa.model_dump() for faixa in body.faixas]
    return sugerir_titulo_descricao(faixas)
