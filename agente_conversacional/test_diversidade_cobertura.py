import pandas as pd
import pytest

from recomendacao.busca import buscar_recomendacoes
from recomendacao.dataset import carregar_dataset
from recomendacao.indice import IndiceSimilaridade

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


def _linha(track_id, genero, artists="Artista", popularity=50, explicit=False, **audio):
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
        f"Faixa {track_id}",
        popularity,
        200000,
        explicit,
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


def _preparar(tmp_path, linhas, monkeypatch, nome="dataset.csv"):
    df_csv = pd.DataFrame(linhas, columns=COLUNAS)
    caminho = tmp_path / nome
    df_csv.to_csv(caminho, index=True)

    df = carregar_dataset(caminho)
    indice = IndiceSimilaridade(df)
    monkeypatch.setattr("recomendacao.busca.carregar_dataset", lambda: df)
    monkeypatch.setattr("recomendacao.busca.construir_indice", lambda: indice)
    return df


def test_diversidade_generos_conta_generos_distintos_no_resultado(tmp_path, monkeypatch):
    linhas = [
        _linha("t1", "pop", popularity=90),
        _linha("t2", "rock", popularity=80),
        _linha("t3", "pop", popularity=70),
        _linha("t4", "jazz", popularity=60),
    ]
    _preparar(tmp_path, linhas, monkeypatch)

    resultado = buscar_recomendacoes(n_resultados=4)

    assert resultado["diversidade_generos"] == 3


def test_diversidade_generos_com_um_genero_so(tmp_path, monkeypatch):
    linhas = [_linha("t1", "pop", popularity=90), _linha("t2", "pop", popularity=80)]
    _preparar(tmp_path, linhas, monkeypatch)

    resultado = buscar_recomendacoes(genero="pop")

    assert resultado["diversidade_generos"] == 1


def test_cobertura_sessao_e_um_quando_nada_foi_mostrado_antes(tmp_path, monkeypatch):
    linhas = [_linha("t1", "pop", popularity=90), _linha("t2", "pop", popularity=80)]
    _preparar(tmp_path, linhas, monkeypatch)

    resultado = buscar_recomendacoes()

    assert resultado["cobertura_sessao"] == pytest.approx(1.0)


def test_cobertura_sessao_reflete_proporcao_de_faixas_novas(tmp_path, monkeypatch):
    linhas = [
        _linha("ja_mostrada", "pop", popularity=90),
        _linha("nova1", "pop", popularity=80),
        _linha("nova2", "pop", popularity=70),
        _linha("nova3", "pop", popularity=60),
    ]
    _preparar(tmp_path, linhas, monkeypatch)

    resultado = buscar_recomendacoes(n_resultados=4, faixas_ja_mostradas=["ja_mostrada"])

    assert resultado["cobertura_sessao"] == pytest.approx(3 / 4)


def test_cobertura_sessao_e_zero_quando_tudo_ja_foi_mostrado(tmp_path, monkeypatch):
    linhas = [_linha("t1", "pop", popularity=90), _linha("t2", "pop", popularity=80)]
    _preparar(tmp_path, linhas, monkeypatch)

    resultado = buscar_recomendacoes(n_resultados=2, faixas_ja_mostradas=["t1", "t2"])

    assert resultado["cobertura_sessao"] == pytest.approx(0.0)


def test_faixas_ja_mostradas_invalido_e_ignorado_sem_quebrar(tmp_path, monkeypatch):
    linhas = [_linha("t1", "pop", popularity=90)]
    _preparar(tmp_path, linhas, monkeypatch)

    resultado = buscar_recomendacoes(faixas_ja_mostradas="nao-e-uma-lista-de-track-ids")

    # string bruta e tratada como entrada invalida (nao explode em
    # caracteres soltos) -> equivale a nao ter passado nada
    assert resultado["cobertura_sessao"] == pytest.approx(1.0)


def test_faixas_ja_mostradas_nao_iteravel_e_ignorado_sem_quebrar(tmp_path, monkeypatch):
    linhas = [_linha("t1", "pop", popularity=90)]
    _preparar(tmp_path, linhas, monkeypatch)

    resultado = buscar_recomendacoes(faixas_ja_mostradas=42)

    assert resultado["cobertura_sessao"] == pytest.approx(1.0)


def test_diversidade_e_cobertura_presentes_mesmo_no_fallback_de_popularidade(tmp_path, monkeypatch):
    linhas = [_linha("t1", "pop", popularity=90), _linha("t2", "rock", popularity=10)]
    _preparar(tmp_path, linhas, monkeypatch)

    resultado = buscar_recomendacoes()  # nenhum sinal -> fallback de popularidade

    assert resultado["diversidade_generos"] == 2
    assert resultado["cobertura_sessao"] == pytest.approx(1.0)


def test_diversidade_e_cobertura_presentes_com_resultado_vazio(tmp_path, monkeypatch):
    linhas = [_linha("t1", "pop", explicit=True, popularity=90)]
    _preparar(tmp_path, linhas, monkeypatch)

    resultado = buscar_recomendacoes(excluir_explicit=True)  # zera os candidatos

    assert resultado["faixas"] == []
    assert resultado["diversidade_generos"] == 0
    assert resultado["cobertura_sessao"] == pytest.approx(0.0)


def test_diversidade_e_cobertura_presentes_com_busca_por_similaridade(tmp_path, monkeypatch):
    linhas = [
        _linha("t1", "pop", energy=0.9, popularity=90),
        _linha("t2", "rock", energy=0.85, popularity=80),
    ]
    _preparar(tmp_path, linhas, monkeypatch)

    resultado = buscar_recomendacoes(energia="alta", faixas_ja_mostradas=["t1"])

    assert resultado["diversidade_generos"] == 2
    assert resultado["cobertura_sessao"] == pytest.approx(0.5)
