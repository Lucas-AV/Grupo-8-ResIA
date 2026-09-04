from urllib.parse import quote

_SCOPES_LIDOS = [
    ("Músicas mais ouvidas (~6 meses)", "user-top-read"),
    ("Últimas faixas tocadas", "user-read-recently-played"),
    ("Faixas salvas/curtidas", "user-library-read"),
    ("Criar playlists na sua conta", "playlist-modify-public playlist-modify-private"),
    ("Salvar faixas em \"Músicas Curtidas\"", "user-library-modify"),
]


def render_consent_page(session_id):
    """Pagina de consentimento exibida antes do redirect pro Spotify (ticket 5.10)."""
    itens = "".join(f"<li>{descricao} (<code>{scope}</code>)</li>" for descricao, scope in _SCOPES_LIDOS)
    safe_session_id = quote(session_id, safe="")
    return f"""<!doctype html>
<html lang="pt-BR">
<head><meta charset="utf-8"><title>Conectar com Spotify</title></head>
<body>
<h1>Conectar sua conta Spotify</h1>
<p>Antes de continuar, veja o que o agente lê da sua conta e pra que usa:</p>
<ul>{itens}</ul>
<p>Usamos isso só pra calcular seu perfil de gosto (média das
características de áudio das faixas que baterem com nosso catálogo) e
personalizar recomendações. Não guardamos seu histórico bruto — só os
tokens de acesso, criptografados; o perfil é recalculado a cada login.
Nenhum dado demográfico é coletado. Você pode desconectar a qualquer
momento.</p>
<p><a href="/auth/login/start?session_id={safe_session_id}">Conectar com Spotify</a></p>
</body>
</html>"""
