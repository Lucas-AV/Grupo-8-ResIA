import logging

import numpy as np

from recomendacao.dataset import FEATURES_AUDIO_NORM, carregar_dataset
from recomendacao.historico_match import casar_historico_com_dataset

logger = logging.getLogger("agente.recomendacao.perfil")


def calcular_perfil_usuario(historico_faixas, dataset=None):
    """Centroide do gosto do usuario (ticket 5.7/KAN-47): casa `historico_faixas`
    (mesmo formato heterogeneo aceito por `casar_historico_com_dataset`, ticket
    5.6/KAN-46 — top tracks / recently played / saved tracks do Spotify) com o
    dataset local e devolve a media de `FEATURES_AUDIO_NORM` das linhas casadas,
    pronta pra ser passada como `perfil_usuario` em
    `recomendacao.busca.buscar_recomendacoes` (blend 70/30 com o sinal da
    consulta).

    Nunca levanta excecao — qualquer falha (historico vazio/None, dataset que
    nao carrega, dataset sem as colunas esperadas, centroide todo-NaN, etc.)
    devolve `None`, o mesmo valor default de `perfil_usuario` em
    `buscar_recomendacoes`. Cobertura zero (nenhuma faixa casada) portanto
    produz o mesmo resultado que nao passar `perfil_usuario` — a chamada
    `buscar_recomendacoes(..., perfil_usuario=calcular_perfil_usuario(...))`
    e sempre segura, mesmo pra usuario anonimo/sem match.

    Retorna um `numpy.ndarray` de shape `(len(FEATURES_AUDIO_NORM),)` (a
    mesma ordem de colunas que `busca.py` espera) ou `None`.
    """
    try:
        df = dataset if dataset is not None else carregar_dataset()
    except Exception:
        logger.warning("falha ao carregar dataset pro perfil de usuario — perfil_usuario=None", exc_info=True)
        return None

    try:
        casamento = casar_historico_com_dataset(historico_faixas, dataset=df)
    except Exception:
        logger.warning("falha ao casar historico com o dataset pro perfil de usuario — perfil_usuario=None", exc_info=True)
        return None

    indices = casamento["indices"]
    if casamento["total_casadas"] == 0 or not indices:
        logger.info("nenhuma faixa do historico casou com o dataset — perfil_usuario=None (mesmo comportamento do anonimo)")
        return None

    try:
        vetor = df.loc[indices, FEATURES_AUDIO_NORM].mean().to_numpy(dtype=float)
    except Exception:
        logger.warning("falha ao calcular o centroide das faixas casadas — perfil_usuario=None", exc_info=True)
        return None

    if vetor.shape != (len(FEATURES_AUDIO_NORM),) or np.isnan(vetor).any():
        logger.warning("centroide invalido (shape/NaN inesperado) — perfil_usuario=None")
        return None

    return vetor
