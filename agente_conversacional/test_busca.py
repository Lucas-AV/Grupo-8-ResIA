import numpy as np
import pandas as pd
import pytest

from recomendacao.busca import _BUCKET_PARA_Z, _montar_vetor_alvo, buscar_recomendacoes
from recomendacao.dataset import FEATURES_AUDIO, FEATURES_AUDIO_NORM, carregar_dataset
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
    """Escreve um dataset.csv pequeno, carrega/normaliza (reaproveitando
    1.1) e monkeypatcha as dependencias de busca.py pra usar esse dataset
    em vez do dataset.csv real cacheado — buscar_recomendacoes nao aceita
    `caminho` (a assinatura e a especificada pelo ticket), entao esse e o
    jeito de isolar os testes do dataset de producao."""
    df_csv = pd.DataFrame(linhas, columns=COLUNAS)
    caminho = tmp_path / nome
    df_csv.to_csv(caminho, index=True)

    df = carregar_dataset(caminho)
    indice = IndiceSimilaridade(df)
    monkeypatch.setattr("recomendacao.busca.carregar_dataset", lambda: df)
    monkeypatch.setattr("recomendacao.busca.construir_indice", lambda: indice)
    return df


def test_aceita_todos_os_parametros_sem_quebrar(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "pop"), _linha("t2", "rock")], monkeypatch)

    resultado = buscar_recomendacoes(
        genero="pop",
        energia="alta",
        valencia="feliz",
        dancabilidade="baixa",
        artista_referencia="Artista",
        excluir_explicit=True,
        n_resultados=5,
        perfil_usuario=[0.0] * len(FEATURES_AUDIO_NORM),
        faixas_ja_mostradas=["t1"],
    )

    assert set(resultado) == {"faixas", "diversidade_generos", "cobertura_sessao", "consulta_efetiva"}
    assert isinstance(resultado["faixas"], list)


def test_faixa_tem_o_schema_documentado(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "pop", artists="Alguem")], monkeypatch)

    faixa = buscar_recomendacoes()["faixas"][0]

    assert set(faixa) == {"track_id", "nome", "artista", "album", "genero"}
    assert faixa["track_id"] == "t1"
    assert faixa["artista"] == "Alguem"


def test_genero_invalido_vira_none_e_nao_filtra(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "pop"), _linha("t2", "rock")], monkeypatch)

    resultado = buscar_recomendacoes(genero="genero-que-nao-existe")

    assert resultado["consulta_efetiva"]["genero"] is None
    assert {f["track_id"] for f in resultado["faixas"]} == {"t1", "t2"}


def test_genero_valido_filtra_candidatos(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "pop"), _linha("t2", "rock")], monkeypatch)

    resultado = buscar_recomendacoes(genero="ROCK")  # case-insensitive

    assert resultado["consulta_efetiva"]["genero"] == "rock"
    assert {f["track_id"] for f in resultado["faixas"]} == {"t2"}


def test_artista_referencia_invalido_vira_none(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "pop", artists="Alguem")], monkeypatch)

    resultado = buscar_recomendacoes(artista_referencia="Artista Que Nao Existe")

    assert resultado["consulta_efetiva"]["artista_referencia"] is None


@pytest.mark.parametrize("energia,valencia,dancabilidade", [("furiosa", None, None), (None, "meh", None), (None, None, 123)])
def test_valores_de_enum_invalidos_viram_none(tmp_path, monkeypatch, energia, valencia, dancabilidade):
    _preparar(tmp_path, [_linha("t1", "pop")], monkeypatch)

    resultado = buscar_recomendacoes(energia=energia, valencia=valencia, dancabilidade=dancabilidade)

    consulta = resultado["consulta_efetiva"]
    assert consulta["energia"] is None
    assert consulta["valencia"] is None
    assert consulta["dancabilidade"] is None


@pytest.mark.parametrize(
    "pedido,esperado",
    [(0, 1), (-5, 1), (100, 30), (1000, 30), ("nao-e-numero", 10), (None, 10), (7, 7)],
)
def test_n_resultados_e_sempre_limitado_entre_1_e_30(tmp_path, monkeypatch, pedido, esperado):
    linhas = [_linha(f"t{i}", "pop", popularity=i) for i in range(40)]
    _preparar(tmp_path, linhas, monkeypatch)

    resultado = buscar_recomendacoes(n_resultados=pedido)

    assert resultado["consulta_efetiva"]["n_resultados"] == esperado
    assert len(resultado["faixas"]) == min(esperado, 40)


def test_excluir_explicit_remove_faixas_explicitas(tmp_path, monkeypatch):
    linhas = [
        _linha("limpa", "pop", popularity=90, explicit=False),
        _linha("explicita", "pop", popularity=99, explicit=True),
    ]
    _preparar(tmp_path, linhas, monkeypatch)

    resultado = buscar_recomendacoes(excluir_explicit=True)

    assert {f["track_id"] for f in resultado["faixas"]} == {"limpa"}


def test_dedup_evita_track_id_duplicado_no_resultado(tmp_path, monkeypatch):
    linhas = [
        _linha("dup", "pop", popularity=80),
        _linha("dup", "dance pop", popularity=80),
        _linha("unica", "rock", popularity=10),
    ]
    _preparar(tmp_path, linhas, monkeypatch)

    resultado = buscar_recomendacoes(n_resultados=30)

    ids = [f["track_id"] for f in resultado["faixas"]]
    assert ids.count("dup") == 1
    assert len(ids) == 2


def test_fallback_por_popularidade_quando_nenhum_sinal(tmp_path, monkeypatch):
    linhas = [
        _linha("baixa", "pop", popularity=10),
        _linha("alta", "pop", popularity=90),
        _linha("media", "pop", popularity=50),
    ]
    _preparar(tmp_path, linhas, monkeypatch)

    resultado = buscar_recomendacoes()

    ids = [f["track_id"] for f in resultado["faixas"]]
    assert ids == ["alta", "media", "baixa"]


def test_artista_referencia_prioriza_faixas_parecidas(tmp_path, monkeypatch):
    linhas = [
        _linha("ref1", "pop", artists="Zayn", energy=0.9, danceability=0.8, tempo=140.0),
        _linha("ref2", "pop", artists="Zayn", energy=0.85, danceability=0.75, tempo=135.0),
        _linha("parecida", "pop", artists="Outro", energy=0.88, danceability=0.78, tempo=138.0),
        _linha("oposta", "pop", artists="Outro2", energy=0.1, danceability=0.1, tempo=70.0),
    ]
    _preparar(tmp_path, linhas, monkeypatch)

    resultado = buscar_recomendacoes(artista_referencia="zayn", n_resultados=4)

    ids_em_ordem = [f["track_id"] for f in resultado["faixas"]]
    assert ids_em_ordem.index("parecida") < ids_em_ordem.index("oposta")


def test_bucket_de_energia_prioriza_faixas_correspondentes(tmp_path, monkeypatch):
    linhas = [
        _linha("alta_energia", "pop", energy=0.95),
        _linha("baixa_energia", "pop", energy=0.05),
        _linha("media_energia", "pop", energy=0.5),
    ]
    _preparar(tmp_path, linhas, monkeypatch)

    resultado = buscar_recomendacoes(energia="alta", n_resultados=3)

    assert resultado["faixas"][0]["track_id"] == "alta_energia"


def test_perfil_usuario_sozinho_direciona_resultado(tmp_path, monkeypatch):
    linhas = [
        _linha("alta_energia", "pop", energy=0.95, danceability=0.9, tempo=150.0),
        _linha("baixa_energia", "pop", energy=0.05, danceability=0.1, tempo=70.0),
    ]
    df = _preparar(tmp_path, linhas, monkeypatch)

    perfil = df.loc[df["track_id"] == "alta_energia", FEATURES_AUDIO_NORM].to_numpy()[0]
    resultado = buscar_recomendacoes(perfil_usuario=perfil, n_resultados=2)

    assert resultado["faixas"][0]["track_id"] == "alta_energia"


def test_perfil_usuario_invalido_e_ignorado_sem_quebrar(tmp_path, monkeypatch):
    linhas = [_linha("baixa", "pop", popularity=10), _linha("alta", "pop", popularity=90)]
    _preparar(tmp_path, linhas, monkeypatch)

    resultado = buscar_recomendacoes(perfil_usuario=[1, 2, 3])  # tamanho errado

    # sem sinal valido nenhum -> cai no fallback de popularidade normalmente
    ids = [f["track_id"] for f in resultado["faixas"]]
    assert ids == ["alta", "baixa"]


def test_montar_vetor_alvo_faz_blend_70_30_com_perfil_usuario():
    perfil = np.full(len(FEATURES_AUDIO), -1.0)

    vetor = _montar_vetor_alvo(
        None, artista_referencia=None, energia="alta", valencia=None, dancabilidade=None, perfil_usuario=perfil
    )

    vetor_bucket_esperado = np.zeros(len(FEATURES_AUDIO))
    vetor_bucket_esperado[FEATURES_AUDIO.index("energy")] = _BUCKET_PARA_Z["alta"]
    esperado = 0.7 * vetor_bucket_esperado + 0.3 * perfil

    np.testing.assert_allclose(vetor, esperado)


def test_nenhum_sinal_e_sem_perfil_usuario_devolve_none():
    assert (
        _montar_vetor_alvo(None, artista_referencia=None, energia=None, valencia=None, dancabilidade=None, perfil_usuario=None)
        is None
    )
