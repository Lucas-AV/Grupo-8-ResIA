class SpotifyAuthError(Exception):
    """Erro base do fluxo OAuth com o Spotify."""


class SpotifyTokenExchangeError(SpotifyAuthError):
    """Levantado quando trocar codigo por token ou renovar o access_token falha."""


class SpotifyNotAuthenticatedError(SpotifyAuthError):
    """Levantado quando nao ha tokens validos pra sessao (nunca logou, ou refresh_token invalido/revogado)."""

    def __init__(self, session_id):
        super().__init__(f"sessao '{session_id}' nao autenticada com o Spotify")
        self.session_id = session_id
