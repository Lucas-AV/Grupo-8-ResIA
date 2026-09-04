import os

# Escopos do Épico 13. Mantidos aqui para a tela de consentimento e OAuth não divergirem.
# playlist-modify-public/private + user-library-modify (ticket 12.1/13.15):
# escrita real na conta — criar playlist (POST /playlist/criar) e salvar
# faixa em "Músicas Curtidas" (POST /explorer/track/{id}/save). Sessões
# autenticadas ANTES dessa mudança têm token sem esses escopos — precisam
# reconectar (logout + login de novo) pra Spotify emitir um token novo com
# permissão de escrita; sem isso as duas ações voltam 403.
SCOPES = (
    "user-top-read user-read-recently-played user-library-read user-follow-read "
    "playlist-read-private user-read-playback-state user-read-currently-playing "
    "user-modify-playback-state playlist-modify-public playlist-modify-private "
    "user-library-modify"
)
AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"


def client_id():
    return os.environ["SPOTIFY_CLIENT_ID"]


def client_secret():
    return os.environ["SPOTIFY_CLIENT_SECRET"]
