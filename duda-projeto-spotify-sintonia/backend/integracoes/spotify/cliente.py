"""Cliente Spotipy: OAuth, top items e associação segura ao catálogo local."""

from __future__ import annotations

import random
from collections.abc import Callable
from datetime import UTC, datetime
from hashlib import sha256
from time import sleep
from typing import Any

import requests
import spotipy
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyOAuth

from backend.configuracao.ambiente import Configuracao

from .catalogo import CatalogoAtributos
from .erros import ErroSpotify, SessaoSpotifyInvalida
from .modelos import (
    ArtistaSpotify,
    ColetaSpotify,
    FaixaSpotify,
    PerfilSpotify,
    PeriodoSpotify,
)

ESCOPOS_SPOTIFY = ("user-top-read", "user-read-private")


class ClienteSpotifyReal:
    """Acesso autenticado, sem uso do endpoint Spotify audio-features removido."""

    def __init__(
        self,
        configuracao: Configuracao,
        *,
        catalogo: CatalogoAtributos | None = None,
        dormir: Callable[[float], None] = sleep,
    ) -> None:
        self.configuracao = configuracao
        self.catalogo = catalogo or CatalogoAtributos()
        self.dormir = dormir

    def url_autorizacao(self, estado: str) -> str:
        return self._oauth(estado=estado).get_authorize_url(state=estado)

    def trocar_codigo(self, codigo: str) -> dict[str, Any]:
        try:
            token = self._oauth().get_access_token(codigo, as_dict=True, check_cache=False)
        except SpotifyException as erro:
            raise self._mapear_erro(erro) from erro
        if not token or "access_token" not in token:
            raise SessaoSpotifyInvalida("O Spotify não retornou um token de acesso válido.")
        return token

    def renovar_se_necessario(self, token_info: dict[str, Any]) -> dict[str, Any]:
        oauth = self._oauth()
        try:
            if oauth.is_token_expired(token_info):
                refresh_token = token_info.get("refresh_token")
                if not refresh_token:
                    raise SessaoSpotifyInvalida()
                return oauth.refresh_access_token(refresh_token)
        except SpotifyException as erro:
            raise self._mapear_erro(erro) from erro
        return token_info

    def coletar(self, token_info: dict[str, Any], periodo: PeriodoSpotify = "medium_term", limite: int = 20) -> ColetaSpotify:
        if limite < 1 or limite > 50:
            raise ValueError("O limite de top items deve estar entre 1 e 50.")
        api = self._criar_api(token_info["access_token"])
        perfil_bruto = self._executar(lambda: api.current_user())
        faixas_brutas = self._executar(lambda: api.current_user_top_tracks(limit=limite, time_range=periodo))
        artistas_brutos = self._executar(lambda: api.current_user_top_artists(limit=limite, time_range=periodo))

        faixas = [self._mapear_faixa(item, posicao) for posicao, item in enumerate(faixas_brutas.get("items", []), start=1)]
        artistas = [self._mapear_artista(item, posicao) for posicao, item in enumerate(artistas_brutos.get("items", []), start=1)]
        avisos = []
        if any(faixa.origem_atributos == "indisponivel" for faixa in faixas):
            avisos.append("Algumas top tracks não foram encontradas no catálogo Kaggle e ficaram sem atributos de áudio.")
        avisos.append("Atributos vêm do catálogo Kaggle local; o endpoint audio-features da Spotify não é utilizado.")
        return ColetaSpotify(
            fonte="spotify_api",
            periodo=periodo,
            coletado_em=datetime.now(UTC),
            perfil=self._mapear_perfil(perfil_bruto),
            top_faixas=faixas,
            top_artistas=artistas,
            avisos=avisos,
        )

    def _oauth(self, estado: str | None = None) -> SpotifyOAuth:
        if not self.configuracao.spotify_client_id or not self.configuracao.spotify_client_secret:
            raise ErroSpotify(
                "Configure SPOTIFY_CLIENT_ID e SPOTIFY_CLIENT_SECRET no arquivo .env para usar o modo real.",
                status_http=503,
                codigo="spotify_nao_configurado",
            )
        return SpotifyOAuth(
            client_id=self.configuracao.spotify_client_id,
            client_secret=self.configuracao.spotify_client_secret,
            redirect_uri=self.configuracao.spotify_redirect_uri,
            scope=" ".join(ESCOPOS_SPOTIFY),
            state=estado,
            open_browser=False,
            requests_timeout=self.configuracao.spotify_timeout_segundos,
        )

    def _criar_api(self, access_token: str) -> spotipy.Spotify:
        return spotipy.Spotify(
            auth=access_token,
            requests_timeout=self.configuracao.spotify_timeout_segundos,
            retries=0,
            status_retries=0,
        )

    def _executar(self, chamada: Callable[[], Any]) -> Any:
        for tentativa in range(self.configuracao.spotify_max_tentativas + 1):
            try:
                return chamada()
            except SpotifyException as erro:
                if erro.http_status == 429 and tentativa < self.configuracao.spotify_max_tentativas:
                    espera = self._retry_after(erro) or (2**tentativa) + random.uniform(0, 0.25)
                    self.dormir(espera)
                    continue
                if erro.http_status in {500, 502, 503, 504} and tentativa < self.configuracao.spotify_max_tentativas:
                    self.dormir((2**tentativa) + random.uniform(0, 0.25))
                    continue
                raise self._mapear_erro(erro) from erro
            except requests.RequestException as erro:
                if tentativa < self.configuracao.spotify_max_tentativas:
                    self.dormir((2**tentativa) + random.uniform(0, 0.25))
                    continue
                raise ErroSpotify("Não foi possível comunicar com o Spotify. Tente novamente em instantes.") from erro
        raise ErroSpotify("Não foi possível comunicar com o Spotify.")

    @staticmethod
    def _retry_after(erro: SpotifyException) -> int | None:
        valor = (erro.headers or {}).get("Retry-After")
        try:
            return max(0, int(valor)) if valor is not None else None
        except (TypeError, ValueError):
            return None

    def _mapear_erro(self, erro: SpotifyException) -> ErroSpotify:
        if erro.http_status == 401:
            return SessaoSpotifyInvalida()
        if erro.http_status == 403:
            return ErroSpotify(
                "O Spotify recusou o acesso. Confirme a allowlist, os escopos e a conta Premium do proprietário do app.",
                status_http=403,
                codigo="spotify_acesso_negado",
            )
        if erro.http_status == 429:
            return ErroSpotify(
                "O limite de requisições do Spotify foi atingido. Aguarde antes de tentar novamente.",
                status_http=429,
                codigo="spotify_rate_limit",
                retry_after=self._retry_after(erro),
            )
        return ErroSpotify("O Spotify não conseguiu concluir a solicitação.", status_http=502, codigo="spotify_erro_api")

    def _mapear_perfil(self, bruto: dict[str, Any]) -> PerfilSpotify:
        identificador = str(bruto.get("account_id") or bruto.get("id") or "spotify-desconhecido")
        imagens = bruto.get("images") or []
        imagem_url = imagens[0].get("url") if imagens and isinstance(imagens[0], dict) else None
        return PerfilSpotify(
            id_pseudonimo=f"spotify-{sha256(identificador.encode()).hexdigest()[:16]}",
            nome_exibicao=bruto.get("display_name"),
            imagem_url=imagem_url,
        )

    def _mapear_faixa(self, bruto: dict[str, Any], posicao: int) -> FaixaSpotify:
        track_id = str(bruto.get("id") or "")
        atributos = self.catalogo.obter(track_id) if track_id else None
        album = bruto.get("album") or {}
        urls = bruto.get("external_urls") or {}
        return FaixaSpotify(
            posicao=posicao,
            track_id=track_id,
            nome=str(bruto.get("name") or "Faixa sem nome"),
            artistas=[str(artista.get("name")) for artista in bruto.get("artists", []) if artista.get("name")],
            album=album.get("name"),
            explicita=bruto.get("explicit"),
            uri=bruto.get("uri"),
            url_spotify=urls.get("spotify"),
            atributos_audio=atributos,
            origem_atributos="catalogo_kaggle" if atributos else "indisponivel",
        )

    @staticmethod
    def _mapear_artista(bruto: dict[str, Any], posicao: int) -> ArtistaSpotify:
        urls = bruto.get("external_urls") or {}
        return ArtistaSpotify(
            posicao=posicao,
            artista_id=str(bruto.get("id") or ""),
            nome=str(bruto.get("name") or "Artista sem nome"),
            generos=[str(genero) for genero in bruto.get("genres", [])],
            url_spotify=urls.get("spotify"),
        )
