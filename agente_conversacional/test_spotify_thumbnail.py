"""Miniatura de capa das faixas recomendadas — usa o oEmbed público da
Spotify (https://open.spotify.com/oembed), que devolve thumbnail_url sem
exigir OAuth/login do usuário. `buscar_thumbnail` nunca levanta exceção:
sem track_id, HTTP != 200, corpo inesperado ou falha de rede degrada pra
None, mesma filosofia defensiva de `recomendacao/spotify_fallback.py` e
`youtube/client.py`."""

import requests

from spotify_auth.thumbnail import buscar_thumbnail
from spotify_auth import thumbnail as thumbnail_module
import pytest


@pytest.fixture(autouse=True)
def _reset_thumbnail_cache():
    # cache em nivel de modulo (mesmo padrao de youtube/client.py) — sem
    # isso, uma consulta cacheada por um teste vazaria pro proximo com o
    # mesmo track_id.
    thumbnail_module._thumbnail_cache.clear()


class _FakeResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    def json(self):
        return self._body


def test_retorna_thumbnail_url_quando_oembed_responde_ok(monkeypatch):
    monkeypatch.setattr(
        requests,
        "get",
        lambda *a, **kw: _FakeResponse(200, {"thumbnail_url": "https://image-cdn.spotifycdn.com/abc.jpg"}),
    )

    assert buscar_thumbnail("0VjIjW4GlUZAMYd2vXMi3b") == "https://image-cdn.spotifycdn.com/abc.jpg"


def test_retorna_none_sem_track_id():
    assert buscar_thumbnail("") is None
    assert buscar_thumbnail(None) is None


def test_retorna_none_em_http_diferente_de_200(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **kw: _FakeResponse(404, {}))

    assert buscar_thumbnail("track-inexistente") is None


def test_retorna_none_quando_corpo_nao_tem_thumbnail_url(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **kw: _FakeResponse(200, {"title": "Alguma faixa"}))

    assert buscar_thumbnail("track-sem-thumb") is None


def test_retorna_none_em_falha_de_rede(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.exceptions.ConnectionError("sem rede")

    monkeypatch.setattr(requests, "get", fake_get)

    assert buscar_thumbnail("track-qualquer") is None


def test_cache_evita_segunda_chamada_http_para_mesmo_track_id(monkeypatch):
    chamadas = []

    def fake_get(*args, **kwargs):
        chamadas.append(1)
        return _FakeResponse(200, {"thumbnail_url": "https://image-cdn.spotifycdn.com/xyz.jpg"})

    monkeypatch.setattr(requests, "get", fake_get)

    primeiro = buscar_thumbnail("track-repetido")
    segundo = buscar_thumbnail("track-repetido")

    assert primeiro == segundo == "https://image-cdn.spotifycdn.com/xyz.jpg"
    assert len(chamadas) == 1
