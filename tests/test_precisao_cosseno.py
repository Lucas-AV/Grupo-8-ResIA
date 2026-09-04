import numpy as np
import pandas as pd

from avaliar_precisao_cosseno import (
    baseline_aleatorio,
    precisao_media_em_k,
    preparar_matriz_unitaria,
    topk_similares,
)


def test_preparar_matriz_unitaria_produz_linhas_unitarias():
    df = pd.DataFrame(
        {
            "danceability": [0.1, 0.9, 0.5, 0.2],
            "energy": [0.2, 0.8, 0.5, 0.1],
            "loudness": [-10, -2, -6, -9],
            "speechiness": [0.05, 0.4, 0.1, 0.05],
            "acousticness": [0.8, 0.05, 0.4, 0.7],
            "instrumentalness": [0.0, 0.0, 0.9, 0.0],
            "liveness": [0.1, 0.3, 0.1, 0.2],
            "valence": [0.3, 0.9, 0.5, 0.2],
            "tempo": [90, 140, 110, 95],
        }
    )
    matriz = preparar_matriz_unitaria(df)
    normas = np.linalg.norm(matriz, axis=1)
    np.testing.assert_allclose(normas, np.ones(len(df)), atol=1e-5)


def test_topk_similares_exclui_a_propria_faixa():
    # Vetores 2D so pra deixar o exemplo facil de raciocinar: linha 0 e 1 sao
    # quase identicas (mesma direcao), linha 2 e ortogonal.
    matriz = np.array(
        [
            [1.0, 0.0],
            [0.99, 0.14],
            [0.0, 1.0],
        ],
        dtype=np.float32,
    )
    matriz = matriz / np.linalg.norm(matriz, axis=1, keepdims=True)

    vizinhos = topk_similares(matriz, indices_consulta=np.array([0]), k=2)

    assert 0 not in vizinhos[0]
    assert vizinhos[0][0] == 1  # linha 1 e mais parecida com a 0 do que a 2


def test_precisao_media_em_k_conta_acertos_de_genero():
    generos = np.array(["pop", "pop", "rock", "pop"])
    indices_consulta = np.array([0, 2])
    # consulta 0 (pop): vizinhos [1 (pop), 3 (pop)] -> 2/2 acertos
    # consulta 2 (rock): vizinhos [0 (pop), 1 (pop)] -> 0/2 acertos
    indices_vizinhos = np.array([[1, 3], [0, 1]])

    precisao = precisao_media_em_k(generos, indices_consulta, indices_vizinhos)

    assert precisao == 0.5


def test_baseline_aleatorio_reflete_concentracao_de_generos():
    generos_concentrados = pd.Series(["pop"] * 9 + ["rock"])
    generos_uniformes = pd.Series(["pop", "rock", "jazz", "funk"])

    assert baseline_aleatorio(generos_concentrados) > baseline_aleatorio(generos_uniformes)
