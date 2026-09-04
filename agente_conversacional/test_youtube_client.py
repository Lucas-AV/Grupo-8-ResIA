"""Ticket 13.12 (KAN-121) — prévia de áudio via YouTube, contornando a
restrição da Spotify (preview_url vem null pra apps criados apos nov/2024,
ver docs/superpowers/specs/2026-09-03-spotify-preview-player-design.md).

`buscar_video_id` nunca levanta excecao: sem YOUTUBE_API_KEY, sem resultado,
ou qualquer falha de rede/HTTP degrada pra `None`, mesma filosofia defensiva
de `recomendacao/spotify_fallback.py`."""

import pytest
import requests

from youtube import client as youtube_client
from youtube.client import buscar_video_id


@pytest.fixture(autouse=True)
def _reset_video_id_cache():
    # cache e um dict em nivel de modulo (mesmo padrao de
    # spotify_auth/app_client.py's _app_token_cache) — sem isso, uma consulta
    # cacheada por um teste vazaria pro proximo que usa a mesma nome/artista.
    youtube_client._video_id_cache.clear()


class _FakeResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    def json(self):
        return self._body


def _mock_busca_ok(monkeypatch, video_id="abc123XYZ"):
    def fake_get(*args, **kwargs):
        return _FakeResponse(200, {"items": [{"id": {"videoId": video_id}}]})

    monkeypatch.setattr(requests, "get", fake_get)


def test_retorna_video_id_quando_busca_tem_resultado(monkeypatch):
    monkeypatch.setenv("YOUTUBE_API_KEY", "chave-teste")
    _mock_busca_ok(monkeypatch, video_id="dQw4w9WgXcQ")

    assert buscar_video_id("Nunca Vou Te Deixar", "Artista X") == "dQw4w9WgXcQ"


def test_retorna_none_sem_api_key_configurada(monkeypatch):
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    _mock_busca_ok(monkeypatch)

    assert buscar_video_id("Qualquer Faixa", "Qualquer Artista") is None


def test_retorna_none_sem_nome_da_faixa(monkeypatch):
    monkeypatch.setenv("YOUTUBE_API_KEY", "chave-teste")
    _mock_busca_ok(monkeypatch)

    assert buscar_video_id("", "Artista X") is None


def test_retorna_none_quando_busca_nao_tem_resultado(monkeypatch):
    monkeypatch.setenv("YOUTUBE_API_KEY", "chave-teste")
    monkeypatch.setattr(requests, "get", lambda *a, **kw: _FakeResponse(200, {"items": []}))

    assert buscar_video_id("Faixa Obscura", "Artista Desconhecido") is None


def test_retorna_none_em_http_diferente_de_200(monkeypatch):
    monkeypatch.setenv("YOUTUBE_API_KEY", "chave-teste")
    monkeypatch.setattr(requests, "get", lambda *a, **kw: _FakeResponse(403, {"error": "quota excedida"}))

    assert buscar_video_id("Faixa", "Artista") is None


def test_retorna_none_em_falha_de_rede(monkeypatch):
    monkeypatch.setenv("YOUTUBE_API_KEY", "chave-teste")

    def fake_get(*args, **kwargs):
        raise requests.exceptions.ConnectionError("sem rede")

    monkeypatch.setattr(requests, "get", fake_get)

    assert buscar_video_id("Faixa", "Artista") is None


def test_cache_evita_segunda_chamada_http_para_mesma_consulta(monkeypatch):
    monkeypatch.setenv("YOUTUBE_API_KEY", "chave-teste")
    chamadas = []

    def fake_get(*args, **kwargs):
        chamadas.append(1)
        return _FakeResponse(200, {"items": [{"id": {"videoId": "video-1"}}]})

    monkeypatch.setattr(requests, "get", fake_get)

    primeiro = buscar_video_id("Faixa Repetida", "Artista Repetido")
    segundo = buscar_video_id("Faixa Repetida", "Artista Repetido")

    assert primeiro == segundo == "video-1"
    assert len(chamadas) == 1
