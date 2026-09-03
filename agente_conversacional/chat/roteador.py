"""Ticket 2.1 — roteador deterministico por regex: reconhece pedidos
simples (sinonimos de genero, humor/energia, intensificadores) e
saudacoes/small talk sem precisar chamar o LLM (secao 5, passo 3 do
pipeline; caso de uso 9).

So resolve "pedidos simples" de fato — mensagens longas/conversacionais
(caso de uso 2, ex.: "algo pra relaxar depois de um dia puxado") caem de
proposito pro `None` (roteador nao resolveu) pra seguir pra extracao via
LLM (ticket 2.2), que tem contexto suficiente pra interpretar frases
livres.
"""

import re
from dataclasses import dataclass
from typing import Literal

from recomendacao.normalizacao import normalizar_texto

RouterTipo = Literal["consulta", "saudacao", "fora_escopo"]


@dataclass(frozen=True)
class RouterMatch:
    """Resultado do roteador. `consulta` so e preenchido quando
    `tipo == "consulta"` — a consulta estruturada ja pronta pra seguir
    direto pro validador (ticket 2.3), pulando a extracao via LLM."""

    tipo: RouterTipo
    consulta: dict | None = None


# Pedidos com mais palavras do que isso nao sao tratados como "pedido
# simples" pelo roteador, mesmo que contenham uma palavra-chave reconhecida
# — evita o roteador "roubar" frases conversacionais que deveriam ir pra
# extracao via LLM (caso de uso 2).
_MAX_PALAVRAS_PEDIDO_SIMPLES = 6

_SAUDACOES = [
    r"\boi\b",
    r"\bola\b",
    r"\bopa\b",
    r"\beae\b",
    r"\be ai\b",
    r"\bbom dia\b",
    r"\bboa tarde\b",
    r"\bboa noite\b",
    r"\btudo bem\b",
    r"\btudo bom\b",
    r"\bcomo vai\b",
    r"\bhello\b",
    r"\bhi\b",
]

# Caso de uso 10 — pedido fora de escopo (o agente so recomenda faixas do
# catalogo, nao compoe musica nem busca letra).
_FORA_DE_ESCOPO = [
    r"\bletra d[ae] musica\b",
    r"\bletra dessa musica\b",
    r"\bcompor\b",
    r"\bcomponha\b",
    r"\bcompoe uma musica\b",
    r"\bcriar uma musica\b",
    r"\bgerar uma musica\b",
    r"\bescrever uma letra\b",
    r"\bescreva uma letra\b",
]

# genero real de `track_genre` -> padroes (aplicados sobre o texto ja
# normalizado por `normalizar_texto`, entao sem acento/pontuacao — um
# hifen em "alt-rock" vira espaco, por isso os padroes aceitam `[\s-]?`).
_SINONIMOS_GENERO = {
    "acoustic": [r"\bacustic"],
    "afrobeat": [r"\bafrobeat"],
    "alt-rock": [r"\balt[\s-]?rock\b"],
    "alternative": [r"\balternativ"],
    "ambient": [r"\bambient\b"],
    "anime": [r"\banime\b"],
    "black-metal": [r"\bblack[\s-]?metal\b"],
    "bluegrass": [r"\bbluegrass\b"],
    "blues": [r"\bblues\b"],
    "brazil": [r"\bbrasileir", r"\bbrazil\b"],
    "breakbeat": [r"\bbreakbeat\b"],
    "british": [r"\bbritanic", r"\bbritish\b"],
    "cantopop": [r"\bcantopop\b"],
    "chicago-house": [r"\bchicago[\s-]?house\b"],
    "children": [r"\binfantil", r"\bcrianc"],
    "chill": [r"\bchill\b"],
    "classical": [r"\bclassic", r"\borquestra\b"],
    "club": [r"\bbalada\b", r"\bclub\b"],
    "comedy": [r"\bcomedia\b", r"\bhumor\b"],
    "country": [r"\bcountry\b"],
    "dance": [r"\bdance\b"],
    "dancehall": [r"\bdancehall\b"],
    "death-metal": [r"\bdeath[\s-]?metal\b"],
    "deep-house": [r"\bdeep[\s-]?house\b"],
    "detroit-techno": [r"\bdetroit[\s-]?techno\b"],
    "disco": [r"\bdisco\b"],
    "disney": [r"\bdisney\b"],
    "drum-and-bass": [r"\bdrum\s?(and|n)\s?bass\b", r"\bdnb\b"],
    "dub": [r"\bdub\b"],
    "dubstep": [r"\bdubstep\b"],
    "edm": [r"\bedm\b", r"\beletronic", r"\belectronic"],
    "electro": [r"\belectro\b", r"\beletro\b"],
}

_MOOD_ENERGIA_ALTA = [r"\bmais anima", r"\bmais agita", r"\banimad[oa]\b", r"\bagitad[oa]\b", r"\benergetic"]
_MOOD_ENERGIA_BAIXA = [
    r"\bmenos anima",
    r"\bmenos agita",
    r"\bmais calm",
    r"\bmais tranquil",
    r"\bmais relax",
    r"\bcalm[oa]\b",
    r"\btranquil",
]
_MOOD_VALENCIA_TRISTE = [r"\bmais triste", r"\btriste\b"]
_MOOD_VALENCIA_FELIZ = [r"\bmais feliz", r"\bmais alegre", r"\bfeliz\b", r"\balegre\b"]
_MOOD_DANCABILIDADE_ALTA = [r"\bdancante\b", r"\bpra dancar\b", r"\bpara dancar\b"]

_EXCLUIR_EXPLICIT = [r"\bsem palavrao", r"\bsem groseria", r"\bsem explicit", r"\bnao quero explicit"]


def rotear(mensagem):
    """Tenta resolver `mensagem` sem chamar o LLM. Devolve `None` quando
    nao reconhece nada (o pipeline segue pra extracao via LLM, ticket
    2.2)."""
    if not isinstance(mensagem, str) or not mensagem.strip():
        return None

    normalizada = normalizar_texto(mensagem)

    if _casa_algum(_SAUDACOES, normalizada):
        return RouterMatch(tipo="saudacao")

    if _casa_algum(_FORA_DE_ESCOPO, normalizada):
        return RouterMatch(tipo="fora_escopo")

    if len(normalizada.split()) > _MAX_PALAVRAS_PEDIDO_SIMPLES:
        return None

    consulta = _montar_consulta(normalizada)
    if consulta is None:
        return None
    return RouterMatch(tipo="consulta", consulta=consulta)


def _casa_algum(padroes, texto):
    return any(re.search(padrao, texto) for padrao in padroes)


def _montar_consulta(normalizada):
    genero = _detectar_genero(normalizada)
    energia = _detectar(normalizada, _MOOD_ENERGIA_ALTA, "alta") or _detectar(normalizada, _MOOD_ENERGIA_BAIXA, "baixa")
    valencia = _detectar(normalizada, _MOOD_VALENCIA_TRISTE, "triste") or _detectar(
        normalizada, _MOOD_VALENCIA_FELIZ, "feliz"
    )
    dancabilidade = _detectar(normalizada, _MOOD_DANCABILIDADE_ALTA, "alta")
    excluir_explicit = _casa_algum(_EXCLUIR_EXPLICIT, normalizada)

    nenhum_sinal = genero is None and energia is None and valencia is None and dancabilidade is None and not excluir_explicit
    if nenhum_sinal:
        return None

    return {
        "genero": genero,
        "energia": energia,
        "valencia": valencia,
        "dancabilidade": dancabilidade,
        "artista_referencia": None,
        "excluir_explicit": excluir_explicit,
        "n_resultados": 10,
    }


def _detectar(texto, padroes, valor):
    return valor if _casa_algum(padroes, texto) else None


def _detectar_genero(texto):
    for genero, padroes in _SINONIMOS_GENERO.items():
        if _casa_algum(padroes, texto):
            return genero
    return None
