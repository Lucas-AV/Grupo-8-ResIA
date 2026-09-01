from pathlib import Path

import pandas as pd
import pytest

from backend.agentes.etl.pipeline import (
    ATRIBUTOS_AUDIO,
    agregar_por_genero,
    carregar_dataset,
    executar_etl,
    normalizar_atributos_audio,
    padronizar_nome_genero,
    tratar_dataset,
)


def _linhas_exemplo() -> pd.DataFrame:
    base = {
        "track_id": ["a", "a", "b", None],
        "artists": ["Artista", "Artista", "Outro", "Sem ID"],
        "album_name": [None, None, "Album B", "Album C"],
        "track_name": ["Faixa A", "Faixa A", "Faixa B", "Faixa C"],
        "popularity": [50, 50, 70, 30],
        "duration_ms": [200000, 200000, 180000, 100000],
        "explicit": [False, False, True, False],
        "key": [1, 1, 2, 3],
        "loudness": [-10.0, -10.0, -5.0, -8.0],
        "mode": [1, 1, 0, 1],
        "tempo": [100.0, 100.0, 140.0, 120.0],
        "time_signature": [4, 4, 4, 4],
        "track_genre": ["Alt-Rock", "alternative rock", "Hip-Hop", "pop"],
    }
    for atributo, valores in {
        "danceability": [0.2, 0.2, 0.8, 0.6],
        "energy": [0.3, 0.3, 0.9, 0.5],
        "speechiness": [0.1, 0.1, 0.2, 0.3],
        "acousticness": [0.8, 0.8, 0.1, 0.4],
        "instrumentalness": [0.0, 0.0, 0.1, 0.0],
        "liveness": [0.2, 0.2, 0.3, 0.4],
        "valence": [0.4, 0.4, 0.9, 0.5],
    }.items():
        base[atributo] = valores
    return pd.DataFrame(base)


def test_padroniza_aliases_conservadores() -> None:
    assert padronizar_nome_genero("Alt-Rock") == "alternative rock"
    assert padronizar_nome_genero("R-N-B") == "r&b"
    assert padronizar_nome_genero(None) == "desconhecido"


def test_trata_nulos_e_consolida_track_id() -> None:
    tratado, relatorio = tratar_dataset(_linhas_exemplo())

    assert tratado["track_id"].tolist() == ["a", "b"]
    assert tratado.loc[0, "generos"] == "alternative rock"
    assert tratado.loc[0, "album_name"] == "desconhecido"
    assert relatorio["linhas_descartadas_campos_obrigatorios"] == 1
    assert relatorio["faixas_consolidadas_por_track_id"] == 1


def test_normaliza_atributos_na_escala_zero_um() -> None:
    tratado, _ = tratar_dataset(_linhas_exemplo())
    normalizado, _ = normalizar_atributos_audio(tratado)
    colunas = [f"{coluna}_norm" for coluna in ATRIBUTOS_AUDIO]

    assert normalizado[colunas].ge(0).all().all()
    assert normalizado[colunas].le(1).all().all()


def test_agrega_generos() -> None:
    tratado, _ = tratar_dataset(_linhas_exemplo())
    normalizado, _ = normalizar_atributos_audio(tratado)
    agregado = agregar_por_genero(normalizado)

    assert set(agregado["genero"]) == {"alternative rock", "hip hop"}
    assert agregado["quantidade_faixas"].sum() == 2


def test_rejeita_csv_sem_schema_obrigatorio(tmp_path: Path) -> None:
    caminho = tmp_path / "invalido.csv"
    pd.DataFrame({"track_id": ["a"]}).to_csv(caminho, index=False)

    with pytest.raises(ValueError, match="colunas obrigatórias"):
        carregar_dataset(caminho)


def test_executar_etl_persiste_artefatos(tmp_path: Path) -> None:
    caminho = tmp_path / "dataset.csv"
    _linhas_exemplo().to_csv(caminho, index=False)

    resultado = executar_etl(
        caminho,
        diretorio_saida=tmp_path / "tratados",
        diretorio_modelos=tmp_path / "modelos",
    )

    assert len(resultado.dados_tratados) == 2
    assert all(caminho.exists() for caminho in resultado.arquivos.values())
