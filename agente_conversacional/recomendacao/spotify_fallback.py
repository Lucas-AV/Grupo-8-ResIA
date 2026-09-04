from spotify_auth.app_client import search_tracks

# Ticket KAN-95: nao ha um SLA formal pra latencia do fallback, mas ele nao
# pode segurar a resposta do agente por muito tempo — timeout curto, e
# qualquer estouro degrada pra lista vazia (ver `buscar_faixas_spotify`).
_TIMEOUT_SEGUNDOS = 5

ORIGEM_SPOTIFY_FALLBACK = "spotify_fallback"


def buscar_faixas_spotify(genero, artista_referencia, n_resultados, excluir_explicit, timeout=None):
    """Complementa a busca local com a Spotify Search API quando o dataset
    local (~31.8k faixas) nao tem cobertura suficiente pro genero/artista
    pedido (ticket KAN-95). Usa so a ordenacao de relevancia da propria
    Spotify — as faixas devolvidas por /search nao tem audio features
    normalizadas (endpoint restrito pra apps criados apos nov/2024, mesma
    limitacao documentada em
    docs/superpowers/specs/2026-09-03-spotify-feb2026-api-changes-design.md),
    entao nao da pra reordenar por similaridade de cosseno nem alimentar
    `recomendacao/indice.py` com elas — so reformatamos pro schema local.

    Nunca levanta excecao: qualquer falha (credenciais ausentes, rede,
    timeout, HTTP != 200, corpo inesperado) degrada pra lista vazia, e a
    busca local segue valendo sozinha — mesma filosofia defensiva dos
    `_validar_*` de `recomendacao/busca.py`."""
    consulta_textual = _montar_consulta_textual(genero, artista_referencia)
    if consulta_textual is None or n_resultados <= 0:
        return []

    try:
        itens = search_tracks(consulta_textual, limit=n_resultados, timeout=timeout or _TIMEOUT_SEGUNDOS)
    except Exception:
        return []

    faixas = []
    for item in itens:
        faixa = _formatar_faixa_spotify(item, genero)
        if faixa is None:
            continue
        if excluir_explicit and faixa["_explicit"]:
            continue
        del faixa["_explicit"]
        faixas.append(faixa)

    return faixas[:n_resultados]


def _montar_consulta_textual(genero, artista_referencia):
    partes = []
    if artista_referencia:
        partes.append(f'artist:"{artista_referencia}"')
    if genero:
        partes.append(f'genre:"{genero}"')
    if not partes:
        return None
    return " ".join(partes)


def _formatar_faixa_spotify(item, genero_consulta):
    if not isinstance(item, dict):
        return None
    track_id = item.get("id")
    nome = item.get("name")
    if not track_id or not nome:
        return None

    artistas = item.get("artists") or []
    nomes_artistas = "; ".join(a.get("name", "") for a in artistas if isinstance(a, dict))
    album = item.get("album") if isinstance(item.get("album"), dict) else {}

    return {
        "track_id": track_id,
        "nome": nome,
        "artista": nomes_artistas,
        "album": album.get("name", ""),
        # A Spotify Search API nao devolve genero por faixa (so por
        # artista, via endpoint separado) — usamos o genero pedido na
        # consulta como melhor aproximacao disponivel sem chamada extra;
        # fica None quando a busca foi so por artista_referencia.
        "genero": genero_consulta,
        "_origem": ORIGEM_SPOTIFY_FALLBACK,
        "_explicit": bool(item.get("explicit", False)),
    }
