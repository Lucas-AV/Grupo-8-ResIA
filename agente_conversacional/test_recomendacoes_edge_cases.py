"""Ticket 1.5 — cobertura formal dos casos de uso e edge cases da tabela
§7 do pipeline que dizem respeito a `buscar_recomendacoes` (nao ao
pipeline conversacional inteiro — roteador/LLM/OAuth ficam fora).

Boa parte dessas combinacoes ja saiu testada organicamente nos tickets
1.3/1.4 (`test_busca.py`, `test_diversidade_cobertura.py`); este arquivo
fecha as combinacoes que faltavam e serve de checklist explicito contra
os criterios de aceite do 1.5:
- [x] uma combinacao de sinal por vez (genero so, atributo so, artista de
      referencia, nenhum sinal) -> genero/artista/nenhum sinal ja em
      test_busca.py; atributo so aqui cobre dancabilidade e valencia
      (energia ja estava em test_busca.py).
- [x] n_resultados fora da faixa valida -> test_busca.py (parametrizado).
- [x] genero/artista invalido vira None, nao quebra -> test_busca.py;
      aqui cobre o caso composto (artista invalido + genero valido).
- [x] track_id duplicado nao aparece duas vezes -> test_busca.py; aqui
      cobre duplicata + busca por similaridade (nao so fallback).
- [x] resultado vazio (nenhuma faixa bate os filtros) nao e erro -> aqui,
      pros dois caminhos (fallback de popularidade e similaridade).
"""

import pandas as pd
import pytest

from recomendacao.busca import buscar_recomendacoes
from recomendacao.dataset import carregar_dataset
from recomendacao.indice import IndiceSimilaridade

COLUNAS = [
    "track_id",
    "artists",
    "album_name",
    "track_name",
    "popularity",
    "duration_ms",
    "explicit",
    "danceability",
    "energy",
    "key",
    "loudness",
    "mode",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "time_signature",
    "track_genre",
]


def _linha(track_id, genero, artists="Artista", popularity=50, explicit=False, **audio):
    padrao = {
        "danceability": 0.5,
        "energy": 0.5,
        "loudness": -8.0,
        "speechiness": 0.05,
        "acousticness": 0.1,
        "instrumentalness": 0.0,
        "liveness": 0.2,
        "valence": 0.4,
        "tempo": 120.0,
    }
    padrao.update(audio)
    return [
        track_id,
        artists,
        "Album",
        f"Faixa {track_id}",
        popularity,
        200000,
        explicit,
        padrao["danceability"],
        padrao["energy"],
        1,
        padrao["loudness"],
        1,
        padrao["speechiness"],
        padrao["acousticness"],
        padrao["instrumentalness"],
        padrao["liveness"],
        padrao["valence"],
        padrao["tempo"],
        4,
        genero,
    ]


def _preparar(tmp_path, linhas, monkeypatch, nome="dataset.csv"):
    df_csv = pd.DataFrame(linhas, columns=COLUNAS)
    caminho = tmp_path / nome
    df_csv.to_csv(caminho, index=True)

    df = carregar_dataset(caminho)
    indice = IndiceSimilaridade(df)
    monkeypatch.setattr("recomendacao.busca.carregar_dataset", lambda: df)
    monkeypatch.setattr("recomendacao.busca.construir_indice", lambda: indice)
    return df


# --- combinacao de sinal: atributo so (dancabilidade e valencia) ---


def test_bucket_de_dancabilidade_prioriza_faixas_correspondentes(tmp_path, monkeypatch):
    linhas = [
        _linha("dancante", "pop", danceability=0.95),
        _linha("parada", "pop", danceability=0.05),
        _linha("mediana", "pop", danceability=0.5),
    ]
    _preparar(tmp_path, linhas, monkeypatch)

    resultado = buscar_recomendacoes(dancabilidade="alta", n_resultados=3)

    assert resultado["faixas"][0]["track_id"] == "dancante"


def test_bucket_de_valencia_prioriza_faixas_correspondentes(tmp_path, monkeypatch):
    linhas = [
        _linha("feliz", "pop", valence=0.95),
        _linha("triste", "pop", valence=0.05),
        _linha("neutra", "pop", valence=0.5),
    ]
    _preparar(tmp_path, linhas, monkeypatch)

    resultado = buscar_recomendacoes(valencia="triste", n_resultados=3)

    assert resultado["faixas"][0]["track_id"] == "triste"


# --- genero/artista invalido: caso composto ---


def test_artista_invalido_com_genero_valido_ainda_filtra_por_genero(tmp_path, monkeypatch):
    linhas = [
        _linha("t1", "rock", popularity=90),
        _linha("t2", "pop", popularity=99),
    ]
    _preparar(tmp_path, linhas, monkeypatch)

    resultado = buscar_recomendacoes(artista_referencia="Artista Que Nao Existe", genero="rock")

    assert resultado["consulta_efetiva"]["artista_referencia"] is None
    assert resultado["consulta_efetiva"]["genero"] == "rock"
    assert {f["track_id"] for f in resultado["faixas"]} == {"t1"}


# --- track_id duplicado tambem nao duplica quando a busca usa similaridade ---


def test_dedup_evita_duplicata_tambem_na_busca_por_similaridade(tmp_path, monkeypatch):
    linhas = [
        _linha("dup", "pop", energy=0.9, popularity=80),
        _linha("dup", "dance pop", energy=0.9, popularity=80),
        _linha("unica", "pop", energy=0.1, popularity=10),
    ]
    _preparar(tmp_path, linhas, monkeypatch)

    resultado = buscar_recomendacoes(energia="alta", n_resultados=30)

    ids = [f["track_id"] for f in resultado["faixas"]]
    assert ids.count("dup") == 1


# --- resultado vazio: caso de uso legitimo, nao e erro (secao 5, passo 6) ---


def test_resultado_vazio_no_fallback_de_popularidade_nao_quebra(tmp_path, monkeypatch):
    linhas = [_linha("t1", "pop", explicit=True)]
    _preparar(tmp_path, linhas, monkeypatch)

    resultado = buscar_recomendacoes(excluir_explicit=True)  # unica faixa e explicita

    assert resultado["faixas"] == []
    assert resultado["consulta_efetiva"]["genero"] is None


def test_resultado_vazio_na_busca_por_similaridade_nao_quebra(tmp_path, monkeypatch):
    linhas = [_linha("t1", "pop", explicit=True, energy=0.9)]
    _preparar(tmp_path, linhas, monkeypatch)

    # energia="alta" monta vetor-alvo (usa similaridade), mas excluir_explicit
    # zera os candidatos -> precisa devolver vazio, nao quebrar
    resultado = buscar_recomendacoes(energia="alta", excluir_explicit=True)

    assert resultado["faixas"] == []
