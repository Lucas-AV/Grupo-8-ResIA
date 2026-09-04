import numpy as np

from recomendacao.dataset import FEATURES_AUDIO, FEATURES_AUDIO_NORM, carregar_dataset
from recomendacao.indice import construir_indice
from recomendacao.normalizacao import normalizar_texto
from recomendacao.spotify_fallback import buscar_faixas_spotify

_ENERGIA_DANCABILIDADE_VALORES = {"baixa", "media", "alta"}
_VALENCIA_VALORES = {"triste", "neutro", "feliz"}

# Mapeamento bucket -> z-score na dimensao correspondente. baixa/triste = -1
# desvio, media/neutro = na media do dataset (0), alta/feliz = +1 desvio.
# Escolha de -1/0/+1 e uma convencao razoavel (nao ha threshold explicito
# especificado) — ajustar se o time tiver um criterio melhor.
_BUCKET_PARA_Z = {"baixa": -1.0, "media": 0.0, "alta": 1.0, "triste": -1.0, "neutro": 0.0, "feliz": 1.0}

_PESO_CONSULTA = 0.7
_PESO_PERFIL_USUARIO = 0.3


def buscar_recomendacoes(
    genero=None,
    energia=None,
    valencia=None,
    dancabilidade=None,
    artista_referencia=None,
    excluir_explicit=False,
    n_resultados=10,
    perfil_usuario=None,
    faixas_ja_mostradas=None,
):
    """Busca deterministica de faixas por similaridade de cosseno (ou, na
    ausencia de qualquer sinal, por popularidade geral). Nunca levanta
    excecao por entrada invalida — cada parametro degrada pro seu
    comportamento padrao (ver `_validar_consulta`).

    `faixas_ja_mostradas` so afeta `cobertura_sessao` (ticket 1.4) — nao
    filtra faixas repetidas do resultado em si, so mede a proporcao de
    faixas novas nele.

    Quando a busca local volta vazia ou mais escassa que `n_resultados`
    (cobertura insuficiente no catalogo local pro genero/artista
    pedido), complementa com a Spotify Search API (ticket KAN-95) — ver
    `_completar_com_spotify`. Faixas assim entram marcadas com
    `_origem: "spotify_fallback"`; faixas do dataset local nao ganham essa
    chave (mantem o schema documentado em `_formatar_faixas` intacto).
    """
    df = carregar_dataset()
    consulta = _validar_consulta(
        df, genero, energia, valencia, dancabilidade, artista_referencia, excluir_explicit, n_resultados
    )
    perfil_usuario_valido = _validar_perfil_usuario(perfil_usuario)
    faixas_ja_mostradas_validas = _validar_faixas_ja_mostradas(faixas_ja_mostradas)

    mascara = _mascara_filtros_rigidos(df, consulta["genero"], consulta["excluir_explicit"])
    candidatos = df[mascara]

    vetor_alvo = _montar_vetor_alvo(
        df,
        artista_referencia=consulta["artista_referencia"],
        energia=consulta["energia"],
        valencia=consulta["valencia"],
        dancabilidade=consulta["dancabilidade"],
        perfil_usuario=perfil_usuario_valido,
    )

    if vetor_alvo is None:
        resultado = candidatos.sort_values("popularity", ascending=False).head(consulta["n_resultados"])
    else:
        resultado = _ranquear_por_similaridade(df, mascara, vetor_alvo, consulta["n_resultados"])

    faixas_locais = _formatar_faixas(resultado)
    faixas_fallback = _completar_com_spotify(consulta, faixas_locais)

    return {
        "faixas": faixas_locais + faixas_fallback,
        "diversidade_generos": _calcular_diversidade_generos(resultado, faixas_fallback),
        "cobertura_sessao": _calcular_cobertura_sessao(resultado, faixas_ja_mostradas_validas, faixas_fallback),
        "consulta_efetiva": consulta,
    }


def _completar_com_spotify(consulta, faixas_locais):
    """Escassez = menos faixas locais do que o `n_resultados` (ja validado
    e limitado a 1..30) pedido — cobre tanto o caso vazio quanto o
    parcialmente coberto, sem precisar de um piso arbitrario separado (na
    pratica, o resultado so fica escasso
    quando o filtro de genero/artista restringe demais). So dispara quando
    ha genero ou artista_referencia validos pra virar uma query de texto —
    sem nenhum sinal, nao ha o que perguntar pro Spotify (ver
    `buscar_faixas_spotify`)."""
    faltam = consulta["n_resultados"] - len(faixas_locais)
    if faltam <= 0:
        return []

    faixas_fallback = buscar_faixas_spotify(
        genero=consulta["genero"],
        artista_referencia=consulta["artista_referencia"],
        n_resultados=faltam,
        excluir_explicit=consulta["excluir_explicit"],
    )

    ids_locais = {faixa["track_id"] for faixa in faixas_locais}
    return [faixa for faixa in faixas_fallback if faixa["track_id"] not in ids_locais]


def _validar_consulta(df, genero, energia, valencia, dancabilidade, artista_referencia, excluir_explicit, n_resultados):
    return {
        "genero": _validar_genero(df, genero),
        "energia": _validar_enum(energia, _ENERGIA_DANCABILIDADE_VALORES),
        "valencia": _validar_enum(valencia, _VALENCIA_VALORES),
        "dancabilidade": _validar_enum(dancabilidade, _ENERGIA_DANCABILIDADE_VALORES),
        "artista_referencia": _validar_artista_referencia(df, artista_referencia),
        "excluir_explicit": bool(excluir_explicit),
        "n_resultados": _validar_n_resultados(n_resultados),
    }


def _validar_genero(df, genero):
    if not isinstance(genero, str):
        return None
    generos_validos = {g.lower(): g for g in df["track_genre"].unique()}
    return generos_validos.get(genero.strip().lower())


def _validar_enum(valor, permitidos):
    if isinstance(valor, str) and valor.strip().lower() in permitidos:
        return valor.strip().lower()
    return None


def _validar_artista_referencia(df, artista_referencia):
    if not isinstance(artista_referencia, str) or not artista_referencia.strip():
        return None
    if not _mascara_artista(df, artista_referencia).any():
        return None
    return artista_referencia


def _validar_n_resultados(n_resultados):
    try:
        n = int(n_resultados)
    except (TypeError, ValueError):
        n = 10
    return max(1, min(30, n))


def _validar_perfil_usuario(perfil_usuario):
    if perfil_usuario is None:
        return None
    try:
        vetor = np.asarray(perfil_usuario, dtype=float)
    except (TypeError, ValueError):
        return None
    if vetor.shape != (len(FEATURES_AUDIO_NORM),) or np.isnan(vetor).any():
        return None
    return vetor


def _validar_faixas_ja_mostradas(faixas_ja_mostradas):
    # str tambem e iteravel (de caracteres) — tratar como lista invalida
    # em vez de explodir em letras soltas que nunca vao bater com um
    # track_id de verdade.
    if faixas_ja_mostradas is None or isinstance(faixas_ja_mostradas, str):
        return set()
    try:
        return {item for item in faixas_ja_mostradas if isinstance(item, str)}
    except TypeError:
        return set()


def _mascara_artista(df, artista_referencia):
    alvo = normalizar_texto(artista_referencia)
    return df["artists"].apply(lambda artistas: alvo in {normalizar_texto(a) for a in artistas.split(";")})


def _mascara_filtros_rigidos(df, genero, excluir_explicit):
    mascara = ~df.duplicated(subset="track_id", keep="first")
    if genero is not None:
        mascara &= df["track_genre"] == genero
    if excluir_explicit:
        mascara &= ~df["explicit"]
    return mascara


def _montar_vetor_alvo(df, artista_referencia, energia, valencia, dancabilidade, perfil_usuario):
    if artista_referencia is not None:
        vetor_base = _centroide_do_artista(df, artista_referencia)
    else:
        vetor_buckets = _vetor_dos_buckets(energia, valencia, dancabilidade)
        if vetor_buckets is not None:
            vetor_base = vetor_buckets
        elif perfil_usuario is not None:
            return perfil_usuario  # unico sinal disponivel, sem blend
        else:
            return None  # nenhum sinal -> fallback de popularidade (ver caller)

    if perfil_usuario is not None:
        return _PESO_CONSULTA * vetor_base + _PESO_PERFIL_USUARIO * perfil_usuario
    return vetor_base


def _centroide_do_artista(df, artista_referencia):
    mascara = _mascara_artista(df, artista_referencia)
    return df.loc[mascara, FEATURES_AUDIO_NORM].mean().to_numpy()


def _vetor_dos_buckets(energia, valencia, dancabilidade):
    if energia is None and valencia is None and dancabilidade is None:
        return None
    vetor = np.zeros(len(FEATURES_AUDIO))
    if energia is not None:
        vetor[FEATURES_AUDIO.index("energy")] = _BUCKET_PARA_Z[energia]
    if dancabilidade is not None:
        vetor[FEATURES_AUDIO.index("danceability")] = _BUCKET_PARA_Z[dancabilidade]
    if valencia is not None:
        vetor[FEATURES_AUDIO.index("valence")] = _BUCKET_PARA_Z[valencia]
    return vetor


def _ranquear_por_similaridade(df, mascara, vetor_alvo, n_resultados):
    indice = construir_indice()
    scores = indice.similaridade(vetor_alvo)

    posicoes_validas = np.flatnonzero(mascara.to_numpy())
    if len(posicoes_validas) == 0:
        return df.iloc[posicoes_validas]

    ordem = np.argsort(-scores[posicoes_validas])[:n_resultados]
    return df.iloc[posicoes_validas[ordem]]


def _calcular_diversidade_generos(resultado, faixas_fallback=()):
    """Ticket 1.4 + KAN-95: faixas do Spotify fallback contam pra
    diversidade com o genero que a Spotify Search API devolveu (nenhum,
    nesse caso — ver `_formatar_faixa_spotify`) — mesma logica de "genero
    distinto visto nesta resposta" que ja valia pro dataset local, so que
    sem exigir uma segunda chamada (endpoint de audio-features/genero por
    faixa da Spotify) so pra alimentar essa metrica."""
    generos_locais = set(resultado["track_genre"].dropna().unique()) if len(resultado) else set()
    generos_fallback = {faixa["genero"] for faixa in faixas_fallback if faixa.get("genero")}
    return len(generos_locais | generos_fallback)


def _calcular_cobertura_sessao(resultado, faixas_ja_mostradas, faixas_fallback=()):
    """Ticket 1.4 + KAN-95: faixas do Spotify fallback tambem foram
    mostradas ao usuario nesta sessao, entao contam pra `cobertura_sessao`
    do mesmo jeito que as locais — a metrica mede "faixas novas na resposta
    atual", nao "faixas novas do dataset local"."""
    total = len(resultado) + len(faixas_fallback)
    if total == 0:
        return 0.0
    novas_locais = int((~resultado["track_id"].isin(faixas_ja_mostradas)).sum()) if len(resultado) else 0
    novas_fallback = sum(1 for faixa in faixas_fallback if faixa["track_id"] not in faixas_ja_mostradas)
    return (novas_locais + novas_fallback) / total


def _formatar_faixas(resultado):
    return [
        {
            "track_id": linha.track_id,
            "nome": linha.track_name,
            "artista": linha.artists,
            "album": linha.album_name,
            "genero": linha.track_genre,
        }
        for linha in resultado.itertuples()
    ]
