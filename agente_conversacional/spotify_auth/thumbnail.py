"""Miniatura de capa das faixas recomendadas.

Usa o oEmbed público da Spotify (https://developer.spotify.com/documentation/embeds,
endpoint sem autenticação: https://open.spotify.com/oembed?url=...) — devolve
`thumbnail_url` (capa do álbum) sem exigir login/token do usuário, ao
contrário de `spotify_auth/explorer.py` (que usa a Web API de verdade com o
token PKCE da sessão). Por isso vive fora de `explorer.py`: nenhuma rota
daqui depende de sessão autenticada."""

import requests

_OEMBED_URL = "https://open.spotify.com/oembed"
_TIMEOUT_SEGUNDOS = 5

# Cache em nivel de modulo (mesmo padrao de youtube/client.py e
# spotify_auth/app_client.py's _app_token_cache) — evita reconsultar a
# mesma faixa a cada card renderizado.
_thumbnail_cache: dict[str, str | None] = {}


def buscar_thumbnail(track_id, timeout=None):
    """Devolve a URL da capa do álbum pra `track_id`, ou None quando o
    track_id vier vazio ou a consulta ao oEmbed falhar (rede, HTTP != 200,
    corpo sem thumbnail_url) — nunca levanta exceção."""
    if not track_id:
        return None

    if track_id in _thumbnail_cache:
        return _thumbnail_cache[track_id]

    thumbnail_url = _consultar_oembed(track_id, timeout)
    _thumbnail_cache[track_id] = thumbnail_url
    return thumbnail_url


def _consultar_oembed(track_id, timeout):
    try:
        resposta = requests.get(
            _OEMBED_URL,
            params={"url": f"https://open.spotify.com/track/{track_id}"},
            timeout=timeout or _TIMEOUT_SEGUNDOS,
        )
    except Exception:
        return None

    if resposta.status_code != 200:
        return None

    try:
        return resposta.json().get("thumbnail_url")
    except Exception:
        return None
