"""Ticket KAN-77 (4.10) — preview de áudio nas faixas recomendadas.

Cobre as duas peças novas: `spotify_auth.app_client.get_tracks` (GET
/tracks em lote) e `recomendacao.busca._enriquecer_com_preview_url` (o
enriquecimento em si, chamado de dentro de `buscar_recomendacoes`).

Mocka `requests.post`/`requests.get` diretamente (mesmo padrão de
test_spotify_client.py e test_busca_spotify_fallback.py) — nenhum teste
aqui bate na Spotify de verdade."""

import pandas as pd
import pytest
import requests

from recomendacao.busca import _enriquecer_com_preview_url, buscar_recomendacoes
from recomendacao.dataset import carregar_dataset
from recomendacao.indice import IndiceSimilaridade
from spotify_auth import app_client
from spotify_auth.app_client import get_tracks

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


def _mock_tracks_ok(monkeypatch, tracks):
    monkeypatch.setattr(requests, "get", lambda *a, **kw: _FakeResponse(200, {"tracks": tracks}))


@pytest.fixture(autouse=True)
def spotify_env(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "client-123")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "secret-456")


@pytest.fixture(autouse=True)
def _reset_app_token_cache():
    # mesmo motivo de test_busca_spotify_fallback.py: o cache de token de
    # app é um dict em nível de módulo, compartilhado entre testes.
    app_client._app_token_cache["access_token"] = None
    app_client._app_token_cache["expires_at"] = 0.0
    yield
    app_client._app_token_cache["access_token"] = None
    app_client._app_token_cache["expires_at"] = 0.0


# --- spotify_auth.app_client.get_tracks ---


def test_get_tracks_devolve_lista_bruta_da_spotify(monkeypatch):
    _mock_token_ok(monkeypatch)
    captured = {}

    def fake_get(url, headers=None, params=None, timeout=None):
        captured["url"] = url
        captured["params"] = params
        captured["headers"] = headers
        return _FakeResponse(200, {"tracks": [{"id": "t1", "preview_url": "https://p.mp3/t1"}]})

    monkeypatch.setattr(requests, "get", fake_get)

    resultado = get_tracks(["t1"])

    assert resultado == [{"id": "t1", "preview_url": "https://p.mp3/t1"}]
    assert captured["url"] == "https://api.spotify.com/v1/tracks"
    assert captured["params"] == {"ids": "t1"}
    assert captured["headers"] == {"Authorization": "Bearer app-token"}


def test_get_tracks_ids_falsy_nao_chamam_a_spotify():
    assert get_tracks([]) == []
    assert get_tracks([None, "", None]) == []


def test_get_tracks_descarta_ids_falsy_misturados_com_validos(monkeypatch):
    _mock_token_ok(monkeypatch)
    captured = {}

    def fake_get(url, headers=None, params=None, timeout=None):
        captured["ids"] = params["ids"]
        return _FakeResponse(200, {"tracks": [{"id": "t1", "preview_url": None}]})

    monkeypatch.setattr(requests, "get", fake_get)

    get_tracks([None, "t1", ""])

    assert captured["ids"] == "t1"


def test_get_tracks_faz_uma_chamada_por_lote_de_ate_50_ids(monkeypatch):
    _mock_token_ok(monkeypatch)
    chamadas = []

    def fake_get(url, headers=None, params=None, timeout=None):
        lote = params["ids"].split(",")
        chamadas.append(lote)
        return _FakeResponse(200, {"tracks": [{"id": tid, "preview_url": None} for tid in lote]})

    monkeypatch.setattr(requests, "get", fake_get)

    ids = [f"id{i}" for i in range(120)]
    resultado = get_tracks(ids)

    assert [len(lote) for lote in chamadas] == [50, 50, 20]
    assert len(resultado) == 120


def test_get_tracks_propaga_falha_http(monkeypatch):
    _mock_token_ok(monkeypatch)
    monkeypatch.setattr(requests, "get", lambda *a, **kw: _FakeResponse(500, {"error": "server_error"}))

    with pytest.raises(RuntimeError):
        get_tracks(["t1"])


def test_get_tracks_propaga_falha_de_rede(monkeypatch):
    _mock_token_ok(monkeypatch)

    def fake_get(*args, **kwargs):
        raise requests.exceptions.Timeout("timeout")

    monkeypatch.setattr(requests, "get", fake_get)

    with pytest.raises(requests.exceptions.Timeout):
        get_tracks(["t1"])


def test_get_tracks_propaga_falha_de_token(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **kw: _FakeResponse(401, {"error": "invalid_client"}))

    with pytest.raises(RuntimeError):
        get_tracks(["t1"])


# --- recomendacao.busca._enriquecer_com_preview_url (unidade) ---


def test_enriquecimento_preenche_preview_url_de_toda_faixa(monkeypatch):
    _mock_token_ok(monkeypatch)
    _mock_tracks_ok(
        monkeypatch,
        [
            {"id": "t1", "preview_url": "https://p.mp3/t1"},
            {"id": "t2", "preview_url": "https://p.mp3/t2"},
        ],
    )

    faixas = [{"track_id": "t1"}, {"track_id": "t2"}]
    resultado = _enriquecer_com_preview_url(faixas)

    assert resultado[0]["preview_url"] == "https://p.mp3/t1"
    assert resultado[1]["preview_url"] == "https://p.mp3/t2"


def test_enriquecimento_parcial_algumas_faixas_sem_preview(monkeypatch):
    # resultado parcial: a Spotify tem preview pra uma faixa, mas nao pra
    # outra (item presente, `preview_url` None — o caso mais comum na
    # pratica, ver ressalva de nov/2024 no docstring de
    # _enriquecer_com_preview_url).
    _mock_token_ok(monkeypatch)
    _mock_tracks_ok(
        monkeypatch,
        [
            {"id": "t1", "preview_url": "https://p.mp3/t1"},
            {"id": "t2", "preview_url": None},
        ],
    )

    faixas = [{"track_id": "t1"}, {"track_id": "t2"}]
    resultado = _enriquecer_com_preview_url(faixas)

    assert resultado[0]["preview_url"] == "https://p.mp3/t1"
    assert resultado[1]["preview_url"] is None


def test_enriquecimento_ignora_entradas_nulas_de_ids_nao_encontrados(monkeypatch):
    # a Spotify devolve null na posicao de um id invalido/removido dentro
    # da lista "tracks" (comportamento documentado do endpoint) — nao
    # pode quebrar o mapeamento id -> preview_url.
    _mock_token_ok(monkeypatch)
    _mock_tracks_ok(monkeypatch, [None, {"id": "t1", "preview_url": "https://p.mp3/t1"}])

    faixas = [{"track_id": "t1"}]
    resultado = _enriquecer_com_preview_url(faixas)

    assert resultado[0]["preview_url"] == "https://p.mp3/t1"


def test_enriquecimento_faixa_sem_track_id_fica_com_preview_url_none(monkeypatch):
    _mock_token_ok(monkeypatch)
    _mock_tracks_ok(monkeypatch, [{"id": "t1", "preview_url": "https://p.mp3/t1"}])

    faixas = [{"track_id": "t1"}, {"track_id": None}, {}]
    resultado = _enriquecer_com_preview_url(faixas)

    assert resultado[0]["preview_url"] == "https://p.mp3/t1"
    assert resultado[1]["preview_url"] is None
    assert resultado[2]["preview_url"] is None


def test_enriquecimento_lista_vazia_nao_chama_a_spotify(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **kw: pytest.fail("nao deveria chamar a Spotify"))
    monkeypatch.setattr(requests, "get", lambda *a, **kw: pytest.fail("nao deveria chamar a Spotify"))

    assert _enriquecer_com_preview_url([]) == []


def test_enriquecimento_falha_de_rede_degrada_para_preview_url_none(monkeypatch):
    def fake_post(*args, **kwargs):
        raise requests.exceptions.ConnectionError("boom")

    monkeypatch.setattr(requests, "post", fake_post)

    faixas = [{"track_id": "t1"}]
    resultado = _enriquecer_com_preview_url(faixas)

    assert resultado[0]["preview_url"] is None


def test_enriquecimento_falha_http_degrada_para_preview_url_none(monkeypatch):
    _mock_token_ok(monkeypatch)
    monkeypatch.setattr(requests, "get", lambda *a, **kw: _FakeResponse(500, {"error": "server_error"}))

    faixas = [{"track_id": "t1"}, {"track_id": "t2"}]
    resultado = _enriquecer_com_preview_url(faixas)

    assert resultado[0]["preview_url"] is None
    assert resultado[1]["preview_url"] is None


def test_enriquecimento_credenciais_ausentes_degrada_para_preview_url_none(monkeypatch):
    monkeypatch.delenv("SPOTIFY_CLIENT_ID", raising=False)
    monkeypatch.delenv("SPOTIFY_CLIENT_SECRET", raising=False)
    monkeypatch.setattr(requests, "post", lambda *a, **kw: pytest.fail("nao deveria chegar a chamar a Spotify"))

    faixas = [{"track_id": "t1"}]
    resultado = _enriquecer_com_preview_url(faixas)

    assert resultado[0]["preview_url"] is None


# --- integração: recomendacao.busca.buscar_recomendacoes ---


def test_buscar_recomendacoes_enriquece_faixas_locais_com_preview_url(tmp_path, monkeypatch):
    _preparar(tmp_path, [_linha("t1", "pop"), _linha("t2", "pop")], monkeypatch)
    _mock_token_ok(monkeypatch)
    _mock_tracks_ok(
        monkeypatch,
        [
            {"id": "t1", "preview_url": "https://p.mp3/t1"},
            {"id": "t2", "preview_url": None},
        ],
    )

    resultado = buscar_recomendacoes(genero="pop", n_resultados=2)

    por_id = {f["track_id"]: f["preview_url"] for f in resultado["faixas"]}
    assert por_id == {"t1": "https://p.mp3/t1", "t2": None}


def test_buscar_recomendacoes_degrada_sem_erro_quando_spotify_falha(tmp_path, monkeypatch):
    """Criterio de aceite: falha da Spotify (rede/HTTP/credenciais) nunca
    derruba a resposta — as faixas voltam normalmente, so sem
    preview_url."""
    _preparar(tmp_path, [_linha("t1", "pop")], monkeypatch)

    def fake_post(*args, **kwargs):
        raise requests.exceptions.ConnectionError("boom")

    monkeypatch.setattr(requests, "post", fake_post)

    resultado = buscar_recomendacoes(genero="pop", n_resultados=1)

    assert resultado["faixas"][0]["track_id"] == "t1"
    assert resultado["faixas"][0]["preview_url"] is None
