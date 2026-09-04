import functools

import numpy as np

from recomendacao.dataset import FEATURES_AUDIO_NORM, carregar_dataset


class IndiceSimilaridade:
    """Estrutura de consulta por similaridade de cosseno. A matriz de
    features (ja padronizada por 1.1) e normalizada linha a linha (norma L2)
    uma unica vez na construcao — cada consulta so faz um produto escalar,
    sem recalcular normalizacao nenhuma."""

    def __init__(self, df):
        self.df = df
        matriz = df[FEATURES_AUDIO_NORM].to_numpy(dtype=float)
        normas = np.linalg.norm(matriz, axis=1)
        normas[normas == 0] = 1  # evita divisao por zero em linha nula
        self._matriz_unitaria = matriz / normas[:, None]

    def similaridade(self, vetor_alvo):
        """Cosseno entre `vetor_alvo` (mesma ordem/tamanho de
        FEATURES_AUDIO_NORM) e cada faixa do dataset, na mesma ordem
        posicional do DataFrame."""
        vetor_alvo = np.asarray(vetor_alvo, dtype=float)
        norma_alvo = np.linalg.norm(vetor_alvo)
        if norma_alvo == 0:
            return np.zeros(len(self.df))
        return self._matriz_unitaria @ (vetor_alvo / norma_alvo)

    def mais_similares(self, vetor_alvo, n=10):
        """Indices posicionais (pra usar com `df.iloc[...]`) das `n` faixas
        mais similares a `vetor_alvo`, em ordem decrescente de
        similaridade."""
        if n <= 0:
            return np.array([], dtype=int)

        scores = self.similaridade(vetor_alvo)
        n = min(n, len(scores))
        indices_top = np.argpartition(-scores, n - 1)[:n]
        return indices_top[np.argsort(-scores[indices_top])]


@functools.lru_cache(maxsize=1)
def construir_indice(caminho=None):
    """Constroi o indice de similaridade uma unica vez por `caminho` — o
    resultado fica cacheado, junto com o dataset carregado (1.1)."""
    return IndiceSimilaridade(carregar_dataset(caminho))
