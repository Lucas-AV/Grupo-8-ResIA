"""Ticket KAN-95 — busca via Spotify Search API como fallback do dataset
local. Cobre: fallback dispara quando a busca local volta vazia/escassa,
NAO dispara quando a busca local ja satisfaz `n_resultados`, falha da
Spotify (rede/HTTP/credenciais) degrada pro resultado local sem quebrar, e
o schema da resposta continua consistente (faixas locais sem `_origem`,
faixas do fallback com `_origem: "spotify_fallback"`).

Mocka `requests.post`/`requests.get` diretamente (mesmo padrao de
test_spotify_client.py) — nenhum teste aqui bate na Spotify de verdade."""

import pandas as pd
import pytest
import requests

from recomendacao.busca import buscar_recomendacoes
from recomendacao.dataset import carregar_dataset
from recomendacao.indice import IndiceSimilaridade
from spotify_auth import app_client

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


def _spotify_track(track_id, nome, artista="Artista Spotify", album="Album Spotify", explicit=False):
    return {
        "id": track_id,
        "name": nome,
        "explicit": explicit,
        "artists": [{"name": artista}],
        "album": {"name": album},
    }


class _FakeResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    def json(self):
        return self._body


def _mock_token_ok(monkeypatch):
    monkeypatch.setattr(
        requests,
        "post",
        lambda *a, **kw: _FakeResponse(200, {"access_token": "app-token", "expires_in": 3600}),
    )


def _mock_search_ok(monkeypatch, itens):
    monkeypatch.setattr(
        requests,
        "get",
        lambda *a, **kw: _FakeResponse(200, {"tracks": {"items": itens}}),
    )


def _mock_token_ok_e_bloqueia_search(monkeypatch):
    """Ticket KAN-77: `buscar_recomendacoes` agora sempre tenta enriquecer
    as faixas com `preview_url` via `GET /tracks` (recomendacao/busca.py),
    mesmo quando o fallback de *busca* (`GET /search`, KAN-95) não
    dispara — então os testes desta seção não podem mais afirmar "a
    Spotify nunca é chamada", só "a Spotify Search API nunca é chamada".
    `GET /tracks` responde vazio (sem preview pra nenhuma faixa), o que
    não afeta as asserções desses testes (track_id/`_origem`)."""
    _mock_token_ok(monkeypatch)

    def fake_get(url, *args, **kwargs):
        if url.endswith("/search"):
            pytest.fail("nao deveria chamar a Spotify Search API (fallback)")
        return _FakeResponse(200, {"tracks": []})

    monkeypatch.setattr(requests, "get", fake_get)


@pytest.fixture(autouse=True)
def spotify_env(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "client-123")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "secret-456")


@pytest.fixture(autouse=True)
def _reset_app_token_cache():
    # o cache de token de app e um dict em nivel de modulo (mesmo padrao de
    # spotify_explorer/spotify_client.py) — sem isso, um teste que popula o
    # cache faria o proximo pular a chamada de token e quebrar o mock dele.
    app_client._app_token_cache["access_token"] = None
    app_client._app_token_cache["expires_at"] = 0.0
    yield
    app_client._app_token_cache["access_token"] = None
    app_client._app_token_cache["expires_at"] = 0.0


# --- fallback dispara quando a busca local e vazia/escassa ---


def test_fallback_dispara_quando_local_vazio(tmp_path, monkeypatch):
    # unica faixa local e explicita -> excluir_explicit zera os candidatos
    _preparar(tmp_path, [_linha("t1", "pop", explicit=True)], monkeypatch)
    _mock_token_ok(monkeypatch)
    _mock_search_ok(monkeypatch, [_spotify_track("sp1", "Musica Spotify")])

    resultado = buscar_recomendacoes(genero="pop", excluir_explicit=True, n_resultados=5)

    ids = [f["track_id"] for f in resultado["faixas"]]
    assert ids == ["sp1"]
    assert resultado["faixas"][0]["_origem"] == "spotify_fallback"


def test_fallback_dispara_quando_local_escasso_e_completa_ate_n_resultados(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("local1", "pop", popularity=90)], monkeypatch)
    _mock_token_ok(monkeypatch)
    _mock_search_ok(
        monkeypatch,
        [_spotify_track("sp1", "Musica 1"), _spotify_track("sp2", "Musica 2"), _spotify_track("sp3", "Musica 3")],
    )

    resultado = buscar_recomendacoes(genero="pop", n_resultados=3)

    ids = [f["track_id"] for f in resultado["faixas"]]
    assert ids[0] == "local1"
    assert set(ids[1:]) <= {"sp1", "sp2", "sp3"}
    assert len(resultado["faixas"]) == 3


def test_fallback_marca_apenas_faixas_do_spotify_com_origem(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("local1", "pop", popularity=90)], monkeypatch)
    _mock_token_ok(monkeypatch)
    _mock_search_ok(monkeypatch, [_spotify_track("sp1", "Musica Spotify")])

    resultado = buscar_recomendacoes(genero="pop", n_resultados=2)

    por_id = {f["track_id"]: f for f in resultado["faixas"]}
    assert "_origem" not in por_id["local1"]
    assert por_id["sp1"]["_origem"] == "spotify_fallback"


def test_fallback_nao_duplica_track_id_ja_presente_localmente(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "pop", popularity=90)], monkeypatch)
    _mock_token_ok(monkeypatch)
    # a Spotify devolve, entre outras, uma faixa com o mesmo id da local
    _mock_search_ok(monkeypatch, [_spotify_track("t1", "Duplicada"), _spotify_track("sp2", "Nova")])

    resultado = buscar_recomendacoes(genero="pop", n_resultados=3)

    ids = [f["track_id"] for f in resultado["faixas"]]
    assert ids.count("t1") == 1
    assert "sp2" in ids


# --- fallback NAO dispara quando a busca local ja tem o suficiente ---


def test_fallback_nao_dispara_quando_local_tem_o_suficiente(tmp_path, monkeypatch):
    linhas = [_linha(f"t{i}", "pop", popularity=i) for i in range(5)]
    _preparar(tmp_path, linhas, monkeypatch)
    _mock_token_ok_e_bloqueia_search(monkeypatch)

    resultado = buscar_recomendacoes(genero="pop", n_resultados=3)

    assert len(resultado["faixas"]) == 3
    assert all("_origem" not in f for f in resultado["faixas"])


def test_fallback_nao_dispara_sem_genero_e_sem_artista_referencia(tmp_path, monkeypatch):
    # local escasso, mas sem genero/artista nao ha query de *busca* pra
    # montar -> o fallback de busca (GET /search) nunca dispara (o
    # enriquecimento de preview_url via GET /tracks, ticket KAN-77, e
    # independente disso e continua acontecendo — ver
    # _mock_token_ok_e_bloqueia_search)
    _preparar(tmp_path, [_linha("t1", "pop", popularity=90)], monkeypatch)
    _mock_token_ok_e_bloqueia_search(monkeypatch)

    resultado = buscar_recomendacoes(n_resultados=5)

    assert [f["track_id"] for f in resultado["faixas"]] == ["t1"]


# --- falha da Spotify degrada graciosamente ---


def test_falha_de_rede_no_token_degrada_para_resultado_local(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "pop", popularity=90)], monkeypatch)

    def fake_post(*args, **kwargs):
        raise requests.exceptions.ConnectionError("boom")

    monkeypatch.setattr(requests, "post", fake_post)

    resultado = buscar_recomendacoes(genero="pop", n_resultados=5)

    assert [f["track_id"] for f in resultado["faixas"]] == ["t1"]


def test_falha_http_no_token_degrada_para_resultado_local(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "pop", popularity=90)], monkeypatch)
    monkeypatch.setattr(requests, "post", lambda *a, **kw: _FakeResponse(401, {"error": "invalid_client"}))

    resultado = buscar_recomendacoes(genero="pop", n_resultados=5)

    assert [f["track_id"] for f in resultado["faixas"]] == ["t1"]


def test_falha_de_rede_na_busca_degrada_para_resultado_local(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "pop", popularity=90)], monkeypatch)
    _mock_token_ok(monkeypatch)

    def fake_get(*args, **kwargs):
        raise requests.exceptions.Timeout("timeout")

    monkeypatch.setattr(requests, "get", fake_get)

    resultado = buscar_recomendacoes(genero="pop", n_resultados=5)

    assert [f["track_id"] for f in resultado["faixas"]] == ["t1"]
    assert resultado["diversidade_generos"] == 1
    assert resultado["cobertura_sessao"] == pytest.approx(1.0)


def test_falha_http_na_busca_degrada_para_resultado_local(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "pop", popularity=90)], monkeypatch)
    _mock_token_ok(monkeypatch)
    monkeypatch.setattr(requests, "get", lambda *a, **kw: _FakeResponse(500, {"error": "server_error"}))

    resultado = buscar_recomendacoes(genero="pop", n_resultados=5)

    assert [f["track_id"] for f in resultado["faixas"]] == ["t1"]


def test_credenciais_ausentes_degrada_para_resultado_local(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "pop", popularity=90)], monkeypatch)
    monkeypatch.delenv("SPOTIFY_CLIENT_ID", raising=False)
    monkeypatch.delenv("SPOTIFY_CLIENT_SECRET", raising=False)
    monkeypatch.setattr(requests, "post", lambda *a, **kw: pytest.fail("nao deveria chegar a chamar a Spotify"))

    resultado = buscar_recomendacoes(genero="pop", n_resultados=5)

    assert [f["track_id"] for f in resultado["faixas"]] == ["t1"]


def test_resposta_sem_json_valido_degrada_para_resultado_local(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "pop", popularity=90)], monkeypatch)
    _mock_token_ok(monkeypatch)

    class _RespostaQuebrada:
        status_code = 200

        def json(self):
            raise ValueError("corpo nao e JSON")

    monkeypatch.setattr(requests, "get", lambda *a, **kw: _RespostaQuebrada())

    resultado = buscar_recomendacoes(genero="pop", n_resultados=5)

    assert [f["track_id"] for f in resultado["faixas"]] == ["t1"]


# --- schema da resposta / metricas ---


def test_diversidade_generos_conta_genero_da_consulta_para_faixas_do_fallback(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "rock", popularity=90)], monkeypatch)
    _mock_token_ok(monkeypatch)
    _mock_search_ok(monkeypatch, [_spotify_track("sp1", "Musica Spotify")])

    resultado = buscar_recomendacoes(genero="rock", n_resultados=2)

    # so um genero distinto no total: "rock" local + "rock" (genero da
    # consulta, atribuido a faixa do fallback por falta de genero por
    # faixa na Spotify Search API)
    assert resultado["diversidade_generos"] == 1


def test_cobertura_sessao_conta_faixas_do_fallback_como_mostradas(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "pop", popularity=90)], monkeypatch)
    _mock_token_ok(monkeypatch)
    _mock_search_ok(monkeypatch, [_spotify_track("sp1", "Musica Spotify")])

    resultado = buscar_recomendacoes(genero="pop", n_resultados=2, faixas_ja_mostradas=["sp1"])

    # 2 faixas no total (1 local + 1 fallback), 1 delas ja mostrada -> 0.5
    assert resultado["cobertura_sessao"] == pytest.approx(0.5)


def test_faixa_do_fallback_tem_as_mesmas_chaves_da_local_mais_origem(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "pop", explicit=True)], monkeypatch)
    _mock_token_ok(monkeypatch)
    _mock_search_ok(monkeypatch, [_spotify_track("sp1", "Musica Spotify", artista="Fulano", album="Otimo Album")])

    resultado = buscar_recomendacoes(genero="pop", excluir_explicit=True, n_resultados=3)

    faixa = resultado["faixas"][0]
    assert set(faixa) == {"track_id", "nome", "artista", "album", "genero", "_origem", "preview_url"}
    assert faixa["artista"] == "Fulano"
    assert faixa["album"] == "Otimo Album"
    assert faixa["genero"] == "pop"


def test_fallback_respeita_excluir_explicit(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "pop", explicit=True)], monkeypatch)
    _mock_token_ok(monkeypatch)
    _mock_search_ok(
        monkeypatch,
        [_spotify_track("sp1", "Explicita", explicit=True), _spotify_track("sp2", "Limpa", explicit=False)],
    )

    resultado = buscar_recomendacoes(genero="pop", excluir_explicit=True, n_resultados=3)

    ids = [f["track_id"] for f in resultado["faixas"]]
    assert "sp1" not in ids
    assert "sp2" in ids


def test_resultado_continua_tendo_as_quatro_chaves_documentadas_com_fallback(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "pop", explicit=True)], monkeypatch)
    _mock_token_ok(monkeypatch)
    _mock_search_ok(monkeypatch, [_spotify_track("sp1", "Musica Spotify")])

    resultado = buscar_recomendacoes(genero="pop", excluir_explicit=True, n_resultados=3)

    assert set(resultado) == {"faixas", "diversidade_generos", "cobertura_sessao", "consulta_efetiva"}
