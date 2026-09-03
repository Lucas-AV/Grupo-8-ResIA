import logging

from recomendacao.dataset import carregar_dataset
from recomendacao.normalizacao import normalizar_texto

logger = logging.getLogger("agente.recomendacao.historico_match")


def casar_historico_com_dataset(historico_faixas, dataset=None):
    """Casa as faixas do historico Spotify do usuario (top tracks /
    recently played / saved tracks — `spotify_auth/history.py`, ticket 5.5)
    com o dataset local, por `track_id` exato e, na falta desse, por nome de
    faixa + artista normalizados (`normalizar_texto`, a mesma regra usada
    pra `artista_referencia` em `busca.py`).

    `historico_faixas` aceita os tres formatos que a API do Spotify devolve
    (heterogeneos entre os tres endpoints de 5.5): um objeto de faixa direto
    (`fetch_top_tracks`) ou um item com a faixa aninhada em `track`
    (`fetch_recently_played`/`fetch_saved_tracks`, junto de `played_at`/
    `added_at`). Nunca levanta excecao — entradas malformadas (None, dict
    sem id/name, artists ausente etc.) sao ignoradas e contam pro
    denominador da cobertura, seguindo o padrao defensivo de
    `busca.py::_validar_*`.

    Retorna um dict com os indices do dataset casados (rotulos de `df.index`,
    prontos pra `df.loc[indices, FEATURES_AUDIO_NORM]` — o centroide em si e
    responsabilidade do ticket 5.7/KAN-47, fora do escopo daqui) e as
    contagens/taxa de cobertura do match:

    {
        "indices": [rotulo_do_indice, ...],   # linhas do dataset casadas, sem duplicatas, em ordem
        "track_ids": [track_id, ...],          # track_id de cada linha em `indices`, mesma ordem
        "total_historico": int,                # itens recebidos em `historico_faixas`
        "total_casadas": int,                  # itens do historico que bateram com alguma linha
        "casadas_por_id": int,
        "casadas_por_nome_artista": int,
        "taxa_cobertura": float,               # total_casadas / total_historico, 0.0 se total_historico == 0
    }
    """
    itens = _validar_historico_faixas(historico_faixas)
    df = dataset if dataset is not None else carregar_dataset()

    resultado_vazio = {
        "indices": [],
        "track_ids": [],
        "total_historico": len(itens),
        "total_casadas": 0,
        "casadas_por_id": 0,
        "casadas_por_nome_artista": 0,
        "taxa_cobertura": 0.0,
    }

    if not itens:
        logger.info("historico vazio — nada pra casar com o dataset")
        return resultado_vazio

    try:
        por_id, por_nome_artista = _indexar_dataset(df)
    except (KeyError, TypeError, AttributeError) as exc:
        logger.warning("dataset invalido/sem colunas esperadas pro match de historico: %s", exc)
        return resultado_vazio

    indices_casados = []
    vistos = set()
    casadas_por_id = 0
    casadas_por_nome_artista = 0

    for item in itens:
        track_id, nome, artistas = _extrair_track(item)

        idx = por_id.get(track_id) if track_id is not None else None
        if idx is not None:
            casadas_por_id += 1
        else:
            idx = _casar_por_nome_artista(por_nome_artista, nome, artistas)
            if idx is not None:
                casadas_por_nome_artista += 1

        if idx is not None and idx not in vistos:
            vistos.add(idx)
            indices_casados.append(idx)

    total_casadas = casadas_por_id + casadas_por_nome_artista
    taxa_cobertura = total_casadas / len(itens) if itens else 0.0

    logger.info(
        "match historico x dataset: %d/%d faixas casadas (por id=%d, por nome+artista=%d) — cobertura=%.1f%%",
        total_casadas,
        len(itens),
        casadas_por_id,
        casadas_por_nome_artista,
        taxa_cobertura * 100,
    )

    track_ids_casados = [df.at[idx, "track_id"] for idx in indices_casados]

    return {
        "indices": indices_casados,
        "track_ids": track_ids_casados,
        "total_historico": len(itens),
        "total_casadas": total_casadas,
        "casadas_por_id": casadas_por_id,
        "casadas_por_nome_artista": casadas_por_nome_artista,
        "taxa_cobertura": taxa_cobertura,
    }


def _validar_historico_faixas(historico_faixas):
    # str e iteravel de caracteres — mesmo cuidado de
    # busca.py::_validar_faixas_ja_mostradas pra nao explodir em letras soltas.
    if historico_faixas is None or isinstance(historico_faixas, str):
        return []
    try:
        return list(historico_faixas)
    except TypeError:
        return []


def _indexar_dataset(df):
    """Indices auxiliares pra match O(1): track_id -> rotulo de linha, e
    (nome_norm, artista_norm) -> rotulo de linha pra qualquer um dos
    artistas listados (coluna `artists` e separada por ';'). Em caso de
    colisao (mesmo track_id ou mesma dupla nome/artista aparecendo em mais
    de uma linha), fica a primeira encontrada — suficiente pro proposito de
    achar *uma* linha representativa da faixa."""
    por_id = {}
    por_nome_artista = {}
    for idx, track_id, nome, artistas in zip(df.index, df["track_id"], df["track_name"], df["artists"]):
        if track_id not in por_id:
            por_id[track_id] = idx
        nome_norm = normalizar_texto(str(nome))
        for artista in str(artistas).split(";"):
            chave = (nome_norm, normalizar_texto(artista))
            por_nome_artista.setdefault(chave, idx)
    return por_id, por_nome_artista


def _extrair_track(item):
    """Devolve (track_id, nome, [artistas...]) a partir de um item de
    historico, aceitando tanto o formato de `fetch_top_tracks` (a faixa e o
    proprio item) quanto o de `fetch_recently_played`/`fetch_saved_tracks`
    (a faixa fica aninhada em `item['track']`). Qualquer coisa fora do
    esperado vira (None, None, []) — nunca levanta excecao."""
    if not isinstance(item, dict):
        return None, None, []

    track = item.get("track") if isinstance(item.get("track"), dict) else item

    track_id = track.get("id")
    if not isinstance(track_id, str) or not track_id:
        track_id = None

    nome = track.get("name")
    if not isinstance(nome, str) or not nome:
        nome = None

    artistas_raw = track.get("artists")
    artistas = []
    if isinstance(artistas_raw, list):
        for artista in artistas_raw:
            if isinstance(artista, dict) and isinstance(artista.get("name"), str):
                artistas.append(artista["name"])

    return track_id, nome, artistas


def _casar_por_nome_artista(por_nome_artista, nome, artistas):
    if nome is None or not artistas:
        return None
    nome_norm = normalizar_texto(nome)
    for artista in artistas:
        idx = por_nome_artista.get((nome_norm, normalizar_texto(artista)))
        if idx is not None:
            return idx
    return None
