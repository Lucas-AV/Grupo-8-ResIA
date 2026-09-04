"""Estima um indice de precisao para o motor de recomendacao por
similaridade de cosseno (agente_conversacional/recomendacao/indice.py).

Nao ha rotulo de relevancia explicito no dataset (nenhuma playlist ou
feedback de usuario) — o proxy usado e leave-one-out: para uma amostra de
faixas, cada faixa vira sua propria consulta (vetor de features padronizado,
igual ao indice real) e um vizinho e considerado "relevante" quando tem o
mesmo track_genre da faixa consulta. E uma aproximacao (duas faixas do mesmo
genero nem sempre soam parecidas, e faixas de generos diferentes podem ser
relevantes), nao uma medida de satisfacao real do usuario.

O baseline_aleatorio (proporcao de faixas do mesmo genero no dataset,
ignorando a propria consulta) contextualiza o numero: precisao_media bem
acima do baseline indica que o cosseno concentra vizinhos mais parecidos do
que um sorteio aleatorio faria.
"""

import numpy as np
import pandas as pd

INPUT_FILE = "data/processed/dataset.csv"
OUTPUT_FILE = "data/analytics/precisao_cosseno.csv"

FEATURES_AUDIO = [
    "danceability",
    "energy",
    "loudness",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
]

VALORES_K = [5, 10, 20]
TAMANHO_AMOSTRA = 3000
SEED = 42


def preparar_matriz_unitaria(df: pd.DataFrame, features: list[str] = FEATURES_AUDIO) -> np.ndarray:
    """Reproduz o pipeline real do indice: padroniza (z-score) as features
    de audio e normaliza cada linha pra norma L2 unitaria — o produto escalar
    entre duas linhas dessa matriz ja e o cosseno entre elas."""
    colunas = df[features]
    media = colunas.mean()
    desvio = colunas.std(ddof=0).replace(0, 1)
    matriz = ((colunas - media) / desvio).to_numpy(dtype=np.float32)

    normas = np.linalg.norm(matriz, axis=1)
    normas[normas == 0] = 1
    return matriz / normas[:, None]


def amostrar_indices_consulta(n_linhas: int, tamanho_amostra: int, seed: int = SEED) -> np.ndarray:
    tamanho = min(tamanho_amostra, n_linhas)
    rng = np.random.default_rng(seed)
    return rng.choice(n_linhas, size=tamanho, replace=False)


def topk_similares(matriz_unitaria: np.ndarray, indices_consulta: np.ndarray, k: int) -> np.ndarray:
    """Para cada indice em `indices_consulta`, os `k` indices (posicionais em
    `matriz_unitaria`) mais similares por cosseno, excluindo a propria
    faixa. Devolve um array (len(indices_consulta), k)."""
    scores = matriz_unitaria[indices_consulta] @ matriz_unitaria.T
    scores[np.arange(len(indices_consulta)), indices_consulta] = -np.inf

    k = min(k, matriz_unitaria.shape[0] - 1)
    parciais = np.argpartition(-scores, k - 1, axis=1)[:, :k]
    ordem = np.argsort(-np.take_along_axis(scores, parciais, axis=1), axis=1)
    return np.take_along_axis(parciais, ordem, axis=1)


def precisao_media_em_k(generos: np.ndarray, indices_consulta: np.ndarray, indices_vizinhos: np.ndarray) -> float:
    """Media, sobre todas as consultas, da fracao de vizinhos no top-K que
    compartilham genero com a faixa consulta (proxy de relevancia)."""
    generos_consulta = generos[indices_consulta][:, None]
    acertos = generos[indices_vizinhos] == generos_consulta
    return float(acertos.mean())


def baseline_aleatorio(generos: pd.Series) -> float:
    """Precisao esperada de um recomendador aleatorio: a chance de duas
    faixas sorteadas ao acaso compartilharem genero, ponderada pelo tamanho
    de cada genero no dataset (soma de p_g^2, ajustada por N-1 em vez de N
    pra excluir a propria faixa)."""
    contagens = generos.value_counts()
    n = len(generos)
    return float(((contagens * (contagens - 1)).sum()) / (n * (n - 1)))


def avaliar(df: pd.DataFrame, valores_k: list[int] = VALORES_K, tamanho_amostra: int = TAMANHO_AMOSTRA) -> pd.DataFrame:
    matriz_unitaria = preparar_matriz_unitaria(df)
    generos = df["track_genre"].to_numpy()
    indices_consulta = amostrar_indices_consulta(len(df), tamanho_amostra)

    baseline = baseline_aleatorio(df["track_genre"])
    k_maximo = max(valores_k)
    vizinhos_k_maximo = topk_similares(matriz_unitaria, indices_consulta, k_maximo)

    linhas = []
    for k in valores_k:
        precisao = precisao_media_em_k(generos, indices_consulta, vizinhos_k_maximo[:, :k])
        linhas.append(
            {
                "k": k,
                "precisao_media": precisao,
                "baseline_aleatorio": baseline,
                "ganho_sobre_baseline": precisao / baseline if baseline > 0 else float("nan"),
            }
        )
    return pd.DataFrame(linhas)


def main() -> None:
    df = pd.read_csv(INPUT_FILE, index_col=0)
    df = df[~df["track_id"].duplicated(keep="first")].reset_index(drop=True)

    resultado = avaliar(df)
    resultado.to_csv(OUTPUT_FILE, index=False)

    print(f"Amostra: {min(TAMANHO_AMOSTRA, len(df))} de {len(df)} faixas (proxy de relevancia: mesmo track_genre)")
    for _, linha in resultado.iterrows():
        print(
            f"  k={int(linha['k']):<3} precisao_media={linha['precisao_media']:.3f}  "
            f"baseline_aleatorio={linha['baseline_aleatorio']:.3f}  "
            f"ganho={linha['ganho_sobre_baseline']:.2f}x"
        )
    print(f"Gerado {OUTPUT_FILE}.")


if __name__ == "__main__":
    main()
