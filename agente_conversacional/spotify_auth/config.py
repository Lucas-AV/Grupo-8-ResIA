import os

# Escopos do Épico 13. Mantidos aqui para a tela de consentimento e OAuth não divergirem.
SCOPES = (
    "user-top-read user-read-recently-played user-library-read user-follow-read "
    "playlist-read-private user-read-playback-state user-read-currently-playing "
    "user-modify-playback-state"
)
AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"


def client_id():
    return os.environ["SPOTIFY_CLIENT_ID"]


def client_secret():
    return os.environ["SPOTIFY_CLIENT_SECRET"]


def redirect_uri():
    return os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8000/auth/callback")
