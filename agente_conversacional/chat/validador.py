"""Ticket 2.3 — valida a consulta estruturada (vinda do roteador, ticket
2.1, ou da extração via LLM, ticket 2.2) contra o schema fixo (seção 4.2
do pipeline) antes de chamar `buscar_recomendacoes`. Campo fora do
domínio esperado vira `None`, nunca rejeita a consulta inteira — mesma
filosofia defensiva de `recomendacao.busca._validar_consulta`, aplicada
como uma etapa própria e explícita do pipeline conversacional."""

from recomendacao.dataset import carregar_dataset
from recomendacao.normalizacao import normalizar_texto

_ENERGIA_DANCABILIDADE_VALORES = {"baixa", "media", "alta"}
_VALENCIA_VALORES = {"triste", "neutro", "feliz"}
_N_RESULTADOS_PADRAO = 10
_N_RESULTADOS_MAXIMO = 30
_N_RESULTADOS_MINIMO = 1

_VALORES_VERDADEIROS = {"true", "1", "sim", "yes"}


def validar_consulta(bruta):
    """Devolve sempre um dict com as sete chaves do schema — nunca
    levanta exceção e nunca descarta a consulta inteira por causa de um
    campo inválido isolado."""
    bruta = bruta if isinstance(bruta, dict) else {}
    return {
        "genero": _validar_genero(bruta.get("genero")),
        "energia": _validar_enum(bruta.get("energia"), _ENERGIA_DANCABILIDADE_VALORES),
        "valencia": _validar_enum(bruta.get("valencia"), _VALENCIA_VALORES),
        "dancabilidade": _validar_enum(bruta.get("dancabilidade"), _ENERGIA_DANCABILIDADE_VALORES),
        "artista_referencia": _validar_artista(bruta.get("artista_referencia")),
        "excluir_explicit": _validar_bool(bruta.get("excluir_explicit")),
        "n_resultados": _validar_n_resultados(bruta.get("n_resultados")),
    }


def _validar_genero(genero):
    """`genero`, se preenchido, precisa bater (case-insensitive) com um
    valor real de `track_genre` no dataset — senão vira `None`."""
    if not isinstance(genero, str) or not genero.strip():
        return None
    df = carregar_dataset()
    generos_validos = {g.lower(): g for g in df["track_genre"].unique()}
    return generos_validos.get(genero.strip().lower())


def _validar_enum(valor, permitidos):
    if isinstance(valor, str) and valor.strip().lower() in permitidos:
        return valor.strip().lower()
    return None


def _validar_artista(artista_referencia):
    """Normaliza `artista_referencia` com a mesma função usada no
    matching do histórico do Spotify (ticket 5.6) — `normalizar_texto`.
    A existência do artista no dataset continua sendo checada dentro de
    `buscar_recomendacoes`, que já degrada pra `None` sem erro."""
    if not isinstance(artista_referencia, str) or not artista_referencia.strip():
        return None
    normalizado = normalizar_texto(artista_referencia)
    return normalizado or None


def _validar_bool(valor):
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        return valor.strip().lower() in _VALORES_VERDADEIROS
    return bool(valor)


def _validar_n_resultados(n_resultados):
    """Edge case da seção 7: `n_resultados` absurdo é limitado a um teto
    razoável (30) antes de chegar no motor de recomendação."""
    try:
        valor = int(n_resultados)
    except (TypeError, ValueError):
        return _N_RESULTADOS_PADRAO
    return max(_N_RESULTADOS_MINIMO, min(_N_RESULTADOS_MAXIMO, valor))
