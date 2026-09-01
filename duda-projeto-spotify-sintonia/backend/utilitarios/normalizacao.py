"""Normalizações simples aprovadas na Fase 0 e portadas do TypeScript."""

import re
import unicodedata


def normalizar_texto(valor: str) -> str:
    sem_acentos = "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", valor)
        if unicodedata.category(caractere) != "Mn"
    )
    return sem_acentos.lower().strip()


def normalizar_genero(valor: str) -> str:
    normalizado = re.sub(r"[_-]+", " ", normalizar_texto(valor))
    return re.sub(r"\s+", " ", normalizado)


def valores_unicos_normalizados(valores: list[str]) -> list[str]:
    vistos: set[str] = set()
    resultado: list[str] = []
    for valor in valores:
        limpo = valor.strip()
        chave = normalizar_texto(limpo)
        if chave and chave not in vistos:
            vistos.add(chave)
            resultado.append(limpo)
    return resultado

