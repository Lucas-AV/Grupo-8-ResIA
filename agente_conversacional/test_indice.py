import time

import numpy as np
import pandas as pd
import pytest

from recomendacao.dataset import FEATURES_AUDIO, FEATURES_AUDIO_NORM, carregar_dataset
from recomendacao.indice import construir_indice

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


def _escrever_csv(tmp_path, linhas, nome):
    df = pd.DataFrame(linhas, columns=COLUNAS)
    caminho = tmp_path / nome
    df.to_csv(caminho, index=True)
    return caminho


def _linha(track_id, genero, **audio):
    valores_padrao = {
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
    valores_padrao.update(audio)
    return [
        track_id,
        "Artista",
        "Album",
        "Faixa",
        50,
        200000,
        False,
        valores_padrao["danceability"],
        valores_padrao["energy"],
        1,
        valores_padrao["loudness"],
        1,
        valores_padrao["speechiness"],
        valores_padrao["acousticness"],
        valores_padrao["instrumentalness"],
        valores_padrao["liveness"],
        valores_padrao["valence"],
        valores_padrao["tempo"],
        4,
        genero,
    ]


def test_indice_e_construido_uma_unica_vez_por_caminho(tmp_path):
    caminho = _escrever_csv(tmp_path, [_linha("t1", "pop"), _linha("t2", "rock")], "uma_vez.csv")

    indice1 = construir_indice(caminho)
    indice2 = construir_indice(caminho)

    assert indice1 is indice2


def test_faixa_identica_e_a_mais_similar_a_si_mesma(tmp_path):
    caminho = _escrever_csv(
        tmp_path,
        [
            _linha("alvo", "pop", danceability=0.9, energy=0.1, tempo=90.0),
            _linha("oposta", "rock", danceability=0.1, energy=0.9, tempo=180.0),
            _linha("parecida", "pop", danceability=0.85, energy=0.15, tempo=95.0),
        ],
        "similaridade.csv",
    )

    df = carregar_dataset(caminho)
    indice = construir_indice(caminho)

    vetor_alvo = df.loc[df["track_id"] == "alvo", FEATURES_AUDIO_NORM].to_numpy()[0]
    posicoes = indice.mais_similares(vetor_alvo, n=3)
    track_ids_em_ordem = df.iloc[posicoes]["track_id"].tolist()

    assert track_ids_em_ordem[0] == "alvo"
    assert track_ids_em_ordem[1] == "parecida"
    assert track_ids_em_ordem[2] == "oposta"


def test_mais_similares_respeita_n_e_ordem_decrescente(tmp_path):
    linhas = [_linha(f"t{i}", "pop", tempo=float(i)) for i in range(10)]
    caminho = _escrever_csv(tmp_path, linhas, "top_n.csv")

    indice = construir_indice(caminho)
    vetor_alvo = np.zeros(len(FEATURES_AUDIO))
    posicoes = indice.mais_similares(vetor_alvo, n=4)

    assert len(posicoes) == 4
    scores = indice.similaridade(vetor_alvo)[posicoes]
    assert list(scores) == sorted(scores, reverse=True)


def test_mais_similares_com_n_maior_que_dataset_nao_quebra(tmp_path):
    caminho = _escrever_csv(tmp_path, [_linha("t1", "pop"), _linha("t2", "rock")], "n_grande.csv")

    indice = construir_indice(caminho)
    posicoes = indice.mais_similares(np.zeros(len(FEATURES_AUDIO)), n=1000)

    assert len(posicoes) == 2


def test_mais_similares_com_n_zero_devolve_vazio(tmp_path):
    caminho = _escrever_csv(tmp_path, [_linha("t1", "pop")], "n_zero.csv")

    indice = construir_indice(caminho)
    posicoes = indice.mais_similares(np.zeros(len(FEATURES_AUDIO)), n=0)

    assert len(posicoes) == 0


def test_vetor_alvo_nulo_nao_quebra(tmp_path):
    caminho = _escrever_csv(tmp_path, [_linha("t1", "pop"), _linha("t2", "rock")], "vetor_nulo.csv")

    indice = construir_indice(caminho)
    scores = indice.similaridade(np.zeros(len(FEATURES_AUDIO)))

    assert (scores == 0).all()


def test_busca_no_dataset_real_fica_abaixo_de_1s():
    indice = construir_indice()
    vetor_alvo = np.zeros(len(FEATURES_AUDIO))

    inicio = time.perf_counter()
    indice.mais_similares(vetor_alvo, n=30)
    duracao = time.perf_counter() - inicio

    assert duracao < 1.0
