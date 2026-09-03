import numpy as np
import pandas as pd
import pytest

from recomendacao.busca import buscar_recomendacoes
from recomendacao.dataset import FEATURES_AUDIO_NORM, carregar_dataset
from recomendacao.indice import IndiceSimilaridade
from recomendacao.perfil import calcular_perfil_usuario

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


def _linha(track_id, track_name, artists="Artista", genero="pop", **audio):
    padrao = {
        "danceability": 0.5,
        "energy": 0.5,
        "loudness": -8.0,
        "speechiness": 0.05,
        "acousticness": 0.1,
        "instrumentalness": 0.0,
        "liveness": 0.2,
        "valence": 0.4,
        "tempo": 120.0,
    }
    padrao.update(audio)
    return [
        track_id,
        artists,
        "Album",
        track_name,
        50,
        200000,
        False,
        padrao["danceability"],
        padrao["energy"],
        1,
        padrao["loudness"],
        1,
        padrao["speechiness"],
        padrao["acousticness"],
        padrao["instrumentalness"],
        padrao["liveness"],
        padrao["valence"],
        padrao["tempo"],
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


def test_historico_vazio_devolve_none(tmp_path):
    df = _dataset(tmp_path, [_linha("t1", "Musica 1")], nome="vazio.csv")

    assert calcular_perfil_usuario([], dataset=df) is None


def test_historico_none_devolve_none(tmp_path):
    df = _dataset(tmp_path, [_linha("t1", "Musica 1")], nome="none.csv")

    assert calcular_perfil_usuario(None, dataset=df) is None


def test_nenhuma_faixa_casada_devolve_none(tmp_path):
    df = _dataset(tmp_path, [_linha("t1", "Musica 1", artists="Artista 1")], nome="sem_match.csv")
    historico = [_top_track("outro-id", "Outra Musica", ["Outro Artista"])]

    assert calcular_perfil_usuario(historico, dataset=df) is None


def test_dataset_default_usa_carregar_dataset_real():
    # sem match (historico vazio) -> None, exercitando o caminho que carrega
    # o dataset.csv real (dataset=None) sem quebrar.
    assert calcular_perfil_usuario([], dataset=None) is None


def test_dataset_que_falha_ao_carregar_nao_explode(monkeypatch):
    def _quebra():
        raise FileNotFoundError("dataset.csv sumiu")

    monkeypatch.setattr("recomendacao.perfil.carregar_dataset", _quebra)

    assert calcular_perfil_usuario([_top_track("t1", "Musica 1", ["Artista"])], dataset=None) is None


def test_matching_que_levanta_excecao_nao_explode(tmp_path, monkeypatch):
    df = _dataset(tmp_path, [_linha("t1", "Musica 1")], nome="matching_quebrado.csv")

    def _quebra(historico_faixas, dataset=None):
        raise RuntimeError("matching quebrado")

    monkeypatch.setattr("recomendacao.perfil.casar_historico_com_dataset", _quebra)

    assert calcular_perfil_usuario([_top_track("t1", "Musica 1", ["Artista"])], dataset=df) is None


def test_centroide_com_nan_e_descartado(tmp_path):
    df = _dataset(
        tmp_path,
        [_linha("t1", "Musica 1", artists="Artista 1"), _linha("t2", "Musica 2", artists="Artista 2")],
        nome="nan.csv",
    )
    # forca uma feature normalizada invalida na linha casada — deve ser
    # detectado defensivamente em vez de devolver um vetor com NaN.
    df.loc[df["track_id"] == "t1", "energy_norm"] = np.nan
    historico = [_top_track("t1", "Musica 1", ["Artista 1"])]

    assert calcular_perfil_usuario(historico, dataset=df) is None


def test_centroide_e_a_media_das_features_normalizadas_das_faixas_casadas(tmp_path):
    df = _dataset(
        tmp_path,
        [
            _linha("t1", "Musica 1", artists="Artista 1", energy=0.2, danceability=0.9),
            _linha("t2", "Musica 2", artists="Artista 2", energy=0.8, danceability=0.1),
            _linha("t3", "Musica 3", artists="Artista 3", energy=0.5, danceability=0.5),
        ],
        nome="centroide.csv",
    )
    historico = [
        _top_track("t1", "Musica 1", ["Artista 1"]),
        _top_track("t2", "Musica 2", ["Artista 2"]),
    ]

    perfil = calcular_perfil_usuario(historico, dataset=df)

    esperado = df.loc[df["track_id"].isin(["t1", "t2"]), FEATURES_AUDIO_NORM].mean().to_numpy()
    assert isinstance(perfil, np.ndarray)
    assert perfil.shape == (len(FEATURES_AUDIO_NORM),)
    np.testing.assert_allclose(perfil, esperado)


def test_faixas_repetidas_no_historico_nao_distorcem_o_centroide(tmp_path):
    df = _dataset(
        tmp_path,
        [_linha("t1", "Musica 1", artists="Artista 1", energy=0.9), _linha("t2", "Musica 2", artists="Artista 2", energy=0.1)],
        nome="repetido.csv",
    )
    # t1 aparece duas vezes no historico, mas so deve entrar uma vez no
    # centroide (mesma linha de dataset, sem duplicar peso).
    historico = [
        _top_track("t1", "Musica 1", ["Artista 1"]),
        _top_track("t1", "Musica 1", ["Artista 1"]),
        _top_track("t2", "Musica 2", ["Artista 2"]),
    ]

    perfil = calcular_perfil_usuario(historico, dataset=df)
    esperado = df.loc[df["track_id"].isin(["t1", "t2"]), FEATURES_AUDIO_NORM].mean().to_numpy()

    np.testing.assert_allclose(perfil, esperado)


def _preparar_busca(tmp_path, linhas, monkeypatch, nome="dataset.csv"):
    df = _dataset(tmp_path, linhas, nome=nome)
    indice = IndiceSimilaridade(df)
    monkeypatch.setattr("recomendacao.busca.carregar_dataset", lambda: df)
    monkeypatch.setattr("recomendacao.busca.construir_indice", lambda: indice)
    return df


def test_cobertura_zero_produz_mesmo_resultado_que_nao_passar_perfil_usuario(tmp_path, monkeypatch):
    """Criterio de aceite do KAN-47: cobertura zero (nenhuma faixa casada)
    resulta em perfil_usuario vazio/None, sem erro — e o comportamento de
    buscar_recomendacoes(perfil_usuario=None) e identico ao de nem passar o
    parametro."""
    _preparar_busca(
        tmp_path,
        [_linha("t1", "Musica 1", genero="pop"), _linha("t2", "Musica 2", genero="rock")],
        monkeypatch,
    )
    historico_sem_match = [_top_track("nunca-visto", "Musica Desconhecida", ["Artista Desconhecido"])]

    perfil = calcular_perfil_usuario(historico_sem_match, dataset=None)
    assert perfil is None

    resultado_com_perfil_none = buscar_recomendacoes(genero="pop", perfil_usuario=perfil)
    resultado_sem_parametro = buscar_recomendacoes(genero="pop")

    assert resultado_com_perfil_none == resultado_sem_parametro


def test_perfil_calculado_influencia_buscar_recomendacoes(tmp_path, monkeypatch):
    df = _preparar_busca(
        tmp_path,
        [
            _linha("t1", "Musica 1", genero="pop", energy=0.9, danceability=0.9, valence=0.9),
            _linha("t2", "Musica 2", genero="pop", energy=0.1, danceability=0.1, valence=0.1),
        ],
        monkeypatch,
        nome="influencia.csv",
    )
    historico = [_top_track("t1", "Musica 1", ["Artista"])]

    perfil = calcular_perfil_usuario(historico, dataset=df)
    assert perfil is not None

    resultado = buscar_recomendacoes(perfil_usuario=perfil, n_resultados=1)

    assert resultado["faixas"][0]["track_id"] == "t1"
