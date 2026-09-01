"""OAuth, clientes e contratos da integração Spotify."""

from .cliente import ESCOPOS_SPOTIFY, ClienteSpotifyReal
from .demo import ClienteSpotifyDemo
from .erros import ErroSpotify, SessaoSpotifyInvalida
from .modelos import ColetaSpotify
from .sessoes import ArmazenamentoSessoesSpotify

__all__ = [
    "ESCOPOS_SPOTIFY",
    "ArmazenamentoSessoesSpotify",
    "ClienteSpotifyDemo",
    "ClienteSpotifyReal",
    "ColetaSpotify",
    "ErroSpotify",
    "SessaoSpotifyInvalida",
]
