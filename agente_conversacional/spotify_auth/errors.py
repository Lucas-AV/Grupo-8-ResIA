class SpotifyAuthError(Exception):
    """Erro base do fluxo OAuth com o Spotify."""


class SpotifyTokenExchangeError(SpotifyAuthError):
    """Levantado quando trocar codigo por token ou renovar o access_token falha."""


class SpotifyNotAuthenticatedError(SpotifyAuthError):
    """Levantado quando nao ha tokens validos pra sessao (nunca logou, ou refresh_token invalido/revogado)."""

    def __init__(self, session_id):
        super().__init__(f"sessao '{session_id}' nao autenticada com o Spotify")
        self.session_id = session_id


class SpotifyPlaylistError(SpotifyAuthError):
    """Levantado quando criar a playlist ou adicionar faixas falha na Spotify Web API (ticket 12.1)."""


class SpotifyExplorerError(SpotifyAuthError):
    """Levantado quando uma chamada de leitura/controle da Spotify Web API falha (Épico 13)."""
