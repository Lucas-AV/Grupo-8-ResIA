import pandas as pd
import pytest

from recomendacao.dataset import carregar_dataset
from recomendacao.historico_match import casar_historico_com_dataset

COLUNAS = [
    "track_id",
    "artists",
    "album_name",
    "track_name",
    "popularity",
    "duration_ms",
    "explicit",
    "danceability",
    "energy",
    "key",
    "loudness",
    "mode",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "time_signature",
    "track_genre",
]


def _linha(track_id, track_name, artists="Artista", genero="pop"):
    return [
        track_id,
        artists,
        "Album",
        track_name,
        50,
        200000,
        False,
        0.5,
        0.5,
        1,
        -8.0,
        1,
        0.05,
        0.1,
        0.0,
        0.2,
        0.4,
        120.0,
        4,
        genero,
    ]


def _dataset(tmp_path, linhas, nome="dataset.csv"):
    df_csv = pd.DataFrame(linhas, columns=COLUNAS)
    caminho = tmp_path / nome
    df_csv.to_csv(caminho, index=True)
    return carregar_dataset(caminho)


def _top_track(track_id, nome, artistas):
    """Formato de `fetch_top_tracks`: a faixa e o proprio item."""
    return {"id": track_id, "name": nome, "artists": [{"name": a} for a in artistas]}


def _played(track_id, nome, artistas, played_at="2026-01-01T00:00:00Z"):
    """Formato de `fetch_recently_played`: a faixa aninhada em 'track'."""
    return {"track": _top_track(track_id, nome, artistas), "played_at": played_at}


def _saved(track_id, nome, artistas, added_at="2026-01-01T00:00:00Z"):
    """Formato de `fetch_saved_tracks`: a faixa aninhada em 'track'."""
    return {"track": _top_track(track_id, nome, artistas), "added_at": added_at}


def test_historico_vazio_devolve_cobertura_zero_sem_explodir(tmp_path):
    df = _dataset(tmp_path, [_linha("t1", "Musica 1")], nome="vazio.csv")

    resultado = casar_historico_com_dataset([], dataset=df)

    assert resultado["indices"] == []
    assert resultado["track_ids"] == []
    assert resultado["total_historico"] == 0
    assert resultado["total_casadas"] == 0
    assert resultado["taxa_cobertura"] == 0.0


def test_historico_none_e_tratado_como_vazio(tmp_path):
    df = _dataset(tmp_path, [_linha("t1", "Musica 1")], nome="none.csv")

    resultado = casar_historico_com_dataset(None, dataset=df)

    assert resultado["total_historico"] == 0
    assert resultado["taxa_cobertura"] == 0.0


def test_match_exato_por_track_id(tmp_path):
    df = _dataset(
        tmp_path,
        [_linha("t1", "Comedy", artists="Gen Hoshino"), _linha("t2", "Ghost", artists="Ben Woodward")],
        nome="por_id.csv",
    )
    historico = [_top_track("t1", "Nome Diferente", ["Artista Diferente"])]

    resultado = casar_historico_com_dataset(historico, dataset=df)

    assert resultado["track_ids"] == ["t1"]
    assert resultado["casadas_por_id"] == 1
    assert resultado["casadas_por_nome_artista"] == 0
    assert resultado["total_casadas"] == 1
    assert resultado["taxa_cobertura"] == pytest.approx(1.0)


def test_fallback_por_nome_e_artista_normalizados_quando_id_nao_bate(tmp_path):
    df = _dataset(
        tmp_path,
        [_linha("dataset-id", "Café com Leite", artists="Legião Urbana")],
        nome="fallback.csv",
    )
    # id do Spotify (efêmero/diferente do dataset) não bate, mas nome+artista
    # batem depois de normalizar (sem acento, minúsculo, sem pontuação).
    historico = [_top_track("spotify-id-nao-relacionado", "cafe com leite!", ["legiao urbana"])]

    resultado = casar_historico_com_dataset(historico, dataset=df)

    assert resultado["track_ids"] == ["dataset-id"]
    assert resultado["casadas_por_id"] == 0
    assert resultado["casadas_por_nome_artista"] == 1
    assert resultado["taxa_cobertura"] == pytest.approx(1.0)


def test_faixa_sem_correspondencia_nao_conta_como_casada(tmp_path):
    df = _dataset(tmp_path, [_linha("t1", "Musica 1", artists="Artista 1")], nome="sem_match.csv")
    historico = [_top_track("outro-id", "Outra Musica", ["Outro Artista"])]

    resultado = casar_historico_com_dataset(historico, dataset=df)

    assert resultado["indices"] == []
    assert resultado["total_historico"] == 1
    assert resultado["total_casadas"] == 0
    assert resultado["taxa_cobertura"] == 0.0


def test_itens_malformados_sao_ignorados_e_contam_no_denominador(tmp_path):
    df = _dataset(tmp_path, [_linha("t1", "Musica 1", artists="Artista 1")], nome="malformado.csv")
    historico = [
        None,
        "string-solta",
        {},
        {"id": 123},  # id nao-string
        {"name": "Musica 1", "artists": "nao-e-uma-lista"},  # artists no formato errado
        _top_track("t1", "Musica 1", ["Artista 1"]),
    ]

    resultado = casar_historico_com_dataset(historico, dataset=df)

    assert resultado["total_historico"] == len(historico)
    assert resultado["total_casadas"] == 1
    assert resultado["track_ids"] == ["t1"]


def test_string_como_historico_e_tratada_como_vazia(tmp_path):
    df = _dataset(tmp_path, [_linha("t1", "Musica 1")], nome="string.csv")

    resultado = casar_historico_com_dataset("nao-e-uma-lista-de-faixas", dataset=df)

    assert resultado["total_historico"] == 0
    assert resultado["indices"] == []


def test_recently_played_e_saved_tracks_tem_faixa_aninhada_em_track(tmp_path):
    df = _dataset(
        tmp_path,
        [_linha("t1", "Musica 1", artists="Artista 1"), _linha("t2", "Musica 2", artists="Artista 2")],
        nome="aninhado.csv",
    )
    historico = [
        _played("t1", "Musica 1", ["Artista 1"]),
        _saved("t2", "Musica 2", ["Artista 2"]),
    ]

    resultado = casar_historico_com_dataset(historico, dataset=df)

    assert set(resultado["track_ids"]) == {"t1", "t2"}
    assert resultado["total_casadas"] == 2
    assert resultado["taxa_cobertura"] == pytest.approx(1.0)


def test_faixas_repetidas_no_historico_nao_duplicam_indice_no_resultado(tmp_path):
    df = _dataset(tmp_path, [_linha("t1", "Musica 1", artists="Artista 1")], nome="repetido.csv")
    historico = [
        _top_track("t1", "Musica 1", ["Artista 1"]),
        _played("t1", "Musica 1", ["Artista 1"]),
    ]

    resultado = casar_historico_com_dataset(historico, dataset=df)

    # cada item do historico conta pra cobertura, mas a linha do dataset so
    # aparece uma vez em `indices`/`track_ids`.
    assert resultado["total_historico"] == 2
    assert resultado["total_casadas"] == 2
    assert resultado["indices"] == [resultado["indices"][0]]
    assert resultado["track_ids"] == ["t1"]


def test_multiplos_artistas_no_dataset_casam_por_qualquer_um_deles(tmp_path):
    df = _dataset(
        tmp_path,
        [_linha("t1", "Say Something", artists="A Great Big World;Christina Aguilera")],
        nome="multi_artista.csv",
    )
    historico = [_top_track("id-diferente", "say something", ["Christina Aguilera"])]

    resultado = casar_historico_com_dataset(historico, dataset=df)

    assert resultado["track_ids"] == ["t1"]
    assert resultado["casadas_por_nome_artista"] == 1


def test_dataset_default_usa_carregar_dataset_real():
    resultado = casar_historico_com_dataset([])

    assert resultado["total_historico"] == 0
    assert resultado["indices"] == []
