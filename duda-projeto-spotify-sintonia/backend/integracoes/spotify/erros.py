"""Erros estruturados e seguros da integração Spotify."""

from __future__ import annotations


class ErroSpotify(Exception):
    def __init__(self, mensagem: str, *, status_http: int = 502, codigo: str = "spotify_indisponivel", retry_after: int | None = None) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status_http = status_http
        self.codigo = codigo
        self.retry_after = retry_after


class SessaoSpotifyInvalida(ErroSpotify):
    def __init__(self, mensagem: str = "A sessão Spotify expirou. Conecte sua conta novamente.") -> None:
        super().__init__(mensagem, status_http=401, codigo="sessao_spotify_invalida")
