"""Ponto de entrada do agente de coleta para dados autorizados do Spotify."""

from backend.integracoes.spotify.cliente import ClienteSpotifyReal
from backend.integracoes.spotify.demo import ClienteSpotifyDemo
from backend.integracoes.spotify.modelos import ColetaSpotify, PeriodoSpotify


def coletar_sinais_spotify(
    cliente: ClienteSpotifyReal | ClienteSpotifyDemo,
    *,
    periodo: PeriodoSpotify = "medium_term",
    limite: int = 20,
    token_info: dict | None = None,
    usuario_demo: str = "ecletico",
) -> ColetaSpotify:
    """Coleta sinais estruturados sem expor tokens aos demais agentes."""

    if isinstance(cliente, ClienteSpotifyDemo):
        return cliente.coletar(usuario_demo, periodo, limite)
    if token_info is None:
        raise ValueError("O modo real exige uma sessão OAuth válida.")
    return cliente.coletar(token_info, periodo, limite)
