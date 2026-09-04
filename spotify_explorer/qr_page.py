import json


def render_qr_page(svg_data_uri, code, frontend_url):
    return f"""<!doctype html>
<html lang="pt-BR">
<head><meta charset="utf-8"><title>Conectar com Spotify (QR)</title></head>
<body>
<h1>Escaneie pra conectar</h1>
<img src="{svg_data_uri}" alt="QR code para login com Spotify" width="300" height="300">
<p id="status">Aguardando alguém escanear...</p>
<script>
const code = {json.dumps(code)};
const frontendUrl = {json.dumps(frontend_url)};

async function poll() {{
  const response = await fetch(`/api/pair/${{code}}/status`);
  const data = await response.json();
  if (data.status === "completed") {{
    window.location.href = frontendUrl;
    return;
  }}
  if (data.status === "expired" || data.status === "not_found") {{
    window.location.reload();
    return;
  }}
  setTimeout(poll, 2000);
}}

poll();
</script>
</body>
</html>"""


def render_pair_error_page(status):
    mensagens = {
        "not_found": "Esse QR code não é válido. Peça um novo.",
    }
    mensagem = mensagens.get(status, "Não foi possível continuar com esse QR code.")
    return f"""<!doctype html>
<html lang="pt-BR">
<head><meta charset="utf-8"><title>QR code inválido</title></head>
<body>
<h1>{mensagem}</h1>
<p><a href="/login/qr">Gerar novo QR code</a></p>
</body>
</html>"""
