from urllib.parse import quote

_SCOPES_LIDOS = [
    ("Músicas mais ouvidas", "user-top-read", "Identifica seus gêneros e artistas preferidos nos últimos ~6 meses.", "🎵"),
    ("Últimas faixas tocadas", "user-read-recently-played", "Entende o que você tem escutado nos momentos mais recentes.", "⏱️"),
    ("Faixas salvas e curtidas", "user-library-read", "Analisa faixas curtidas da sua biblioteca para calibrar o perfil.", "💚"),
    ("Criar playlists na sua conta", "playlist-modify-public playlist-modify-private", "Permite salvar seleções do agente como novas playlists.", "📑"),
    ("Salvar faixas em Músicas Curtidas", "user-library-modify", "Adiciona faixas recomendadas aos seus favoritos com 1 clique.", "⭐"),
]


def render_consent_page(session_id: str) -> str:
    """Página de consentimento e login com Spotify (ticket 5.10 / Ticket KAN-150 redesign)."""
    safe_session_id = quote(session_id, safe="")

    permissoes_html = "".join(
        f"""
        <div class="permission-item">
          <div class="permission-icon" aria-hidden="true">{icone}</div>
          <div class="permission-text">
            <div class="permission-title-row">
              <strong>{descricao}</strong>
              <code class="scope-tag">{scope.split()[0]}</code>
            </div>
            <p>{detalhe}</p>
          </div>
        </div>
        """
        for descricao, scope, detalhe, icone in _SCOPES_LIDOS
    )

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Conectar com Spotify — SyntonIA</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-base: #0c0c0c;
      --bg-canvas: #121212;
      --bg-surface: #181818;
      --bg-surface-elevated: #242424;
      --bg-surface-hover: #2a2a2a;
      --spotify-green: #1db954;
      --spotify-green-hover: #1ed760;
      --spotify-green-glow: rgba(29, 185, 84, 0.28);
      --text-primary: #ffffff;
      --text-secondary: #b3b3b3;
      --text-muted: #727272;
      --border-subtle: rgba(255, 255, 255, 0.08);
      --radius-sm: 10px;
      --radius-md: 16px;
      --radius-lg: 24px;
      --radius-pill: 9999px;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      background-color: var(--bg-base);
      background-image: 
        radial-gradient(circle at 50% 0%, rgba(29, 185, 84, 0.15), transparent 45%),
        radial-gradient(circle at 80% 80%, rgba(16, 185, 129, 0.08), transparent 40%);
      color: var(--text-primary);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px 16px;
    }}

    .auth-card {{
      background: rgba(24, 24, 24, 0.92);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      max-width: 580px;
      width: 100%;
      padding: 36px 32px;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6), 0 0 30px rgba(29, 185, 84, 0.1);
      animation: cardIn 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }}

    @keyframes cardIn {{
      from {{ opacity: 0; transform: translateY(16px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    .auth-header {{
      text-align: center;
      margin-bottom: 28px;
    }}

    .brand-pill {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(29, 185, 84, 0.12);
      border: 1px solid rgba(29, 185, 84, 0.3);
      padding: 6px 14px;
      border-radius: var(--radius-pill);
      color: var(--spotify-green);
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      margin-bottom: 16px;
    }}

    .brand-pill svg {{
      width: 16px;
      height: 16px;
      fill: currentColor;
    }}

    .auth-header h1 {{
      font-size: 1.65rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      margin-bottom: 8px;
    }}

    .auth-header p {{
      color: var(--text-secondary);
      font-size: 0.9rem;
      line-height: 1.5;
    }}

    .permissions-section {{
      display: flex;
      flex-direction: column;
      gap: 10px;
      margin-bottom: 24px;
    }}

    .permission-item {{
      display: flex;
      align-items: flex-start;
      gap: 14px;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-sm);
      padding: 14px 16px;
      transition: border-color 0.2s, transform 0.2s;
    }}

    .permission-item:hover {{
      border-color: rgba(29, 185, 84, 0.4);
      transform: translateY(-1px);
    }}

    .permission-icon {{
      font-size: 1.25rem;
      line-height: 1;
      padding-top: 2px;
      flex-shrink: 0;
    }}

    .permission-text {{
      flex: 1;
    }}

    .permission-title-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 4px;
    }}

    .permission-title-row strong {{
      font-size: 0.88rem;
      color: var(--text-primary);
    }}

    .scope-tag {{
      font-family: monospace;
      font-size: 0.68rem;
      color: var(--text-muted);
      background: rgba(255, 255, 255, 0.06);
      padding: 2px 6px;
      border-radius: 4px;
      border: 1px solid var(--border-subtle);
    }}

    .permission-text p {{
      color: var(--text-secondary);
      font-size: 0.78rem;
      line-height: 1.4;
    }}

    .privacy-notice {{
      background: rgba(29, 185, 84, 0.06);
      border-left: 3px solid var(--spotify-green);
      border-radius: 6px;
      padding: 12px 14px;
      margin-bottom: 28px;
      font-size: 0.8rem;
      color: var(--text-secondary);
      line-height: 1.5;
    }}

    .privacy-notice strong {{
      color: var(--text-primary);
    }}

    .auth-actions {{
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}

    .btn-connect {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      width: 100%;
      padding: 14px 24px;
      border-radius: var(--radius-pill);
      background: var(--spotify-green);
      color: #000000;
      font-size: 0.95rem;
      font-weight: 700;
      text-decoration: none;
      cursor: pointer;
      border: none;
      transition: background-color 0.2s, transform 0.2s, box-shadow 0.2s;
      box-shadow: 0 4px 16px var(--spotify-green-glow);
    }}

    .btn-connect:hover {{
      background: var(--spotify-green-hover);
      transform: translateY(-2px);
      box-shadow: 0 6px 22px rgba(29, 185, 84, 0.4);
    }}

    .btn-connect svg {{
      width: 20px;
      height: 20px;
      fill: currentColor;
    }}

    .btn-cancel {{
      display: block;
      text-align: center;
      width: 100%;
      padding: 10px;
      color: var(--text-muted);
      font-size: 0.84rem;
      font-weight: 500;
      text-decoration: none;
      transition: color 0.2s;
    }}

    .btn-cancel:hover {{
      color: var(--text-primary);
      text-decoration: underline;
    }}

    .auth-footer {{
      margin-top: 22px;
      text-align: center;
      font-size: 0.72rem;
      color: var(--text-muted);
    }}
  </style>
</head>
<body>
  <main class="auth-card">
    <header class="auth-header">
      <div class="brand-pill">
        <svg viewBox="0 0 24 24">
          <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.485 17.307c-.215.353-.675.466-1.027.25-2.813-1.718-6.353-2.107-10.523-1.155-.403.092-.806-.16-.898-.564-.092-.403.16-.806.564-.898 4.566-1.042 8.487-.6 11.634 1.34.352.216.465.675.25 1.027zm1.464-3.26c-.27.44-.847.58-1.288.31-3.22-1.98-8.127-2.55-11.936-1.393-.497.15-1.028-.135-1.18-.63-.15-.497.135-1.028.63-1.18 4.354-1.32 9.774-.688 13.464 1.584.44.27.58.847.31 1.288zm.126-3.41c-3.86-2.29-10.224-2.5-13.882-1.39-.59.18-1.22-.16-1.4-.75-.18-.59.16-1.22.75-1.4 4.21-1.28 11.23-1.04 15.68 1.6.53.31.7.99.39 1.52-.31.53-.99.7-1.52.39z"/>
        </svg>
        <span>SyntonIA · Spotify OAuth</span>
      </div>
      <h1>Conectar sua conta Spotify</h1>
      <p>Autorize a integração para recomendações personalizadas com base no seu gosto musical e criação de playlists.</p>
    </header>

    <section class="permissions-section" aria-label="Permissões solicitadas">
      {permissoes_html}
    </section>

    <aside class="privacy-notice">
      <strong>Privacidade e Segurança:</strong> Seus dados são usados unicamente para calcular o perfil acústico e calibrar as recomendações. Não salvamos histórico bruto, nenhum dado demográfico é coletado e os tokens são protegidos com criptografia. Você pode desconectar a qualquer momento.
    </aside>

    <div class="auth-actions">
      <a href="/auth/login/start?session_id={safe_session_id}" class="btn-connect" id="btn-consent-login">
        <svg viewBox="0 0 24 24">
          <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.485 17.307c-.215.353-.675.466-1.027.25-2.813-1.718-6.353-2.107-10.523-1.155-.403.092-.806-.16-.898-.564-.092-.403.16-.806.564-.898 4.566-1.042 8.487-.6 11.634 1.34.352.216.465.675.25 1.027zm1.464-3.26c-.27.44-.847.58-1.288.31-3.22-1.98-8.127-2.55-11.936-1.393-.497.15-1.028-.135-1.18-.63-.15-.497.135-1.028.63-1.18 4.354-1.32 9.774-.688 13.464 1.584.44.27.58.847.31 1.288zm.126-3.41c-3.86-2.29-10.224-2.5-13.882-1.39-.59.18-1.22-.16-1.4-.75-.18-.59.16-1.22.75-1.4 4.21-1.28 11.23-1.04 15.68 1.6.53.31.7.99.39 1.52-.31.53-.99.7-1.52.39z"/>
        </svg>
        <span>Conectar com Spotify</span>
      </a>
      <a href="/" class="btn-cancel">Voltar para o Chat</a>
    </div>

    <footer class="auth-footer">
      ResIA Grupo 8 · Agente de Recomendação Musical
    </footer>
  </main>
</body>
</html>"""
