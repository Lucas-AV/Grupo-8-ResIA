import re
import unicodedata


def normalizar_texto(valor):
    """Lowercase, sem acento, sem pontuacao — usado tanto pra casar
    `artista_referencia` (1.3) quanto pro fuzzy match do historico Spotify
    com o dataset local (secao 3.5 do pipeline, ticket 5.6), pra manter os
    dois usando a mesma regra de normalizacao."""
    sem_acento = unicodedata.normalize("NFKD", valor).encode("ascii", "ignore").decode("ascii")
    apenas_alfanumerico = re.sub(r"[^a-z0-9\s]", " ", sem_acento.lower())
    return re.sub(r"\s+", " ", apenas_alfanumerico).strip()
