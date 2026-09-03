import pandas as pd
import pytest

from recomendacao.dataset import FEATURES_AUDIO_NORM, carregar_dataset

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


def _escrever_csv(tmp_path, linhas, nome="dataset.csv"):
    df = pd.DataFrame(linhas, columns=COLUNAS)
    caminho = tmp_path / nome
    df.to_csv(caminho, index=True)
    return caminho


def _linha(track_id, genero, danceability=0.5, energy=0.5, tempo=120.0):
    return [
        track_id,
        "Artista",
        "Album",
        "Faixa",
        50,
        200000,
        False,
        danceability,
        energy,
        1,
        -8.0,
        1,
        0.05,
        0.1,
        0.0,
        0.2,
        0.4,
        tempo,
        4,
        genero,
    ]


def test_carrega_dataset_uma_unica_vez_por_caminho(tmp_path):
    caminho = _escrever_csv(
        tmp_path,
        [_linha("t1", "pop"), _linha("t2", "rock")],
        nome="uma_vez.csv",
    )

    df1 = carregar_dataset(caminho)
    df2 = carregar_dataset(caminho)

    assert df1 is df2


def test_colunas_de_audio_sao_padronizadas(tmp_path):
    caminho = _escrever_csv(
        tmp_path,
        [
            _linha("t1", "pop", danceability=0.2, energy=0.9, tempo=80.0),
            _linha("t2", "rock", danceability=0.8, energy=0.1, tempo=160.0),
            _linha("t3", "jazz", danceability=0.5, energy=0.5, tempo=120.0),
        ],
        nome="padronizacao.csv",
    )

    df = carregar_dataset(caminho)

    assert set(FEATURES_AUDIO_NORM).issubset(df.columns)
    for coluna_variada in ("danceability", "energy", "tempo"):
        normalizada = f"{coluna_variada}_norm"
        assert df[normalizada].mean() == pytest.approx(0.0, abs=1e-9)
        assert df[normalizada].std(ddof=0) == pytest.approx(1.0)
        # coluna original preservada na escala crua, nao sobrescrita
        assert df[coluna_variada].between(0, 1000).all()


def test_padronizacao_nao_quebra_com_coluna_constante(tmp_path):
    caminho = _escrever_csv(
        tmp_path,
        [
            _linha("t1", "pop", tempo=120.0),
            _linha("t2", "rock", tempo=120.0),
        ],
        nome="constante.csv",
    )

    df = carregar_dataset(caminho)

    assert (df["tempo_norm"] == 0).all()
    assert not df["tempo_norm"].isna().any()


def test_marca_duplicatas_de_track_id_sem_remover_linhas(tmp_path):
    caminho = _escrever_csv(
        tmp_path,
        [
            _linha("t1", "pop"),
            _linha("t1", "dance pop"),  # mesma faixa, genero diferente
            _linha("t2", "rock"),
        ],
        nome="duplicatas.csv",
    )

    df = carregar_dataset(caminho)

    assert len(df) == 3
    assert df.loc[df["track_id"] == "t1", "track_id_duplicado"].all()
    assert not df.loc[df["track_id"] == "t2", "track_id_duplicado"].any()


def test_carrega_dataset_real_do_repositorio():
    df = carregar_dataset()

    assert len(df) > 0
    assert set(FEATURES_AUDIO_NORM).issubset(df.columns)
    assert df["track_id_duplicado"].any()
