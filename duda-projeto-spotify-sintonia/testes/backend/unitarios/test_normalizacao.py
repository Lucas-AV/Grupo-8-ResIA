from backend.utilitarios.normalizacao import (
    normalizar_genero,
    normalizar_texto,
    valores_unicos_normalizados,
)


def test_normaliza_acentos_caixa_e_hifens() -> None:
    assert normalizar_texto("  Eletrônica  ") == "eletronica"
    assert normalizar_genero("Alternative-Rock") == "alternative rock"


def test_remove_duplicatas_preservando_primeiro_valor() -> None:
    assert valores_unicos_normalizados(["MPB", " mpb ", "Pop"]) == ["MPB", "Pop"]

