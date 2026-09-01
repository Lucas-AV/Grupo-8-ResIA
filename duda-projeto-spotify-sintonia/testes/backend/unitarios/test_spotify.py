import pytest
from fastapi.testclient import TestClient
from spotipy.exceptions import SpotifyException

from backend.api import ContextoSpotify, criar_aplicacao
from backend.configuracao.ambiente import Configuracao
from backend.integracoes.spotify.catalogo import CatalogoAtributos
from backend.integracoes.spotify.cliente import ESCOPOS_SPOTIFY, ClienteSpotifyReal
from backend.integracoes.spotify.demo import ClienteSpotifyDemo
from backend.integracoes.spotify.erros import ErroSpotify
from backend.integracoes.spotify.sessoes import ArmazenamentoSessoesSpotify


class CatalogoFalso:
    def obter(self, track_id: str):
        if track_id == "track-1":
            from backend.integracoes.spotify.modelos import AtributosSpotify

            return AtributosSpotify(danceability=0.5, danceability_norm=0.5)
        return None


class ApiFalsa:
    def current_user(self):
        return {"account_id": "conta-1", "display_name": "Pessoa Teste", "images": []}

    def current_user_top_tracks(self, **_):
        return {
            "items": [
                {"id": "track-1", "name": "Faixa", "artists": [{"name": "Artista"}], "album": {"name": "Album"}, "explicit": False, "external_urls": {"spotify": "url"}},
                {"id": "track-ausente", "name": "Sem catálogo", "artists": [], "album": {}},
            ]
        }

    def current_user_top_artists(self, **_):
        return {"items": [{"id": "artist-1", "name": "Artista", "genres": ["pop"]}]}


def _configuracao(**valores):
    padrao = {
        "spotify_client_id": "id",
        "spotify_client_secret": "segredo",
        "spotify_modo": "real",
        "spotify_max_tentativas": 1,
    }
    return Configuracao(
        **(padrao | valores),
    )


def test_demo_oferece_tres_personas_com_atributos() -> None:
    cliente = ClienteSpotifyDemo()
    coleta = cliente.coletar("energetico")

    assert cliente.listar_usuarios() == ["acustico", "ecletico", "energetico"]
    assert coleta.fonte == "demo"
    assert coleta.top_faixas[0].origem_atributos == "demo"
    assert coleta.top_faixas[0].atributos_audio is not None


def test_sessoes_nao_persistem_token_fora_da_memoria() -> None:
    sessoes = ArmazenamentoSessoesSpotify()
    identificador, estado = sessoes.criar()
    sessoes.salvar_token(identificador, {"access_token": "segredo"})

    assert sessoes.obter(identificador).estado == estado  # type: ignore[union-attr]
    assert sessoes.obter(identificador).token_info == {"access_token": "segredo"}  # type: ignore[union-attr]
    sessoes.remover(identificador)
    assert sessoes.obter(identificador) is None


def test_cliente_real_associa_catalogo_e_tolera_faixa_ausente() -> None:
    cliente = ClienteSpotifyReal(_configuracao(), catalogo=CatalogoFalso(), dormir=lambda _: None)
    cliente._criar_api = lambda _: ApiFalsa()  # type: ignore[method-assign]

    coleta = cliente.coletar({"access_token": "token"})

    assert coleta.perfil.id_pseudonimo.startswith("spotify-")
    assert coleta.top_faixas[0].origem_atributos == "catalogo_kaggle"
    assert coleta.top_faixas[1].origem_atributos == "indisponivel"
    assert "user-top-read" in ESCOPOS_SPOTIFY
    assert "user-read-private" in ESCOPOS_SPOTIFY


def test_rate_limit_respeita_retry_after() -> None:
    esperas: list[float] = []
    cliente = ClienteSpotifyReal(_configuracao(), dormir=esperas.append)
    chamadas = 0

    def chamada():
        nonlocal chamadas
        chamadas += 1
        if chamadas == 1:
            raise SpotifyException(429, -1, "limite", headers={"Retry-After": "2"})
        return "ok"

    assert cliente._executar(chamada) == "ok"
    assert esperas == [2]


def test_rate_limit_sem_tentativas_vira_erro_estruturado() -> None:
    cliente = ClienteSpotifyReal(_configuracao(spotify_max_tentativas=0), dormir=lambda _: None)

    with pytest.raises(ErroSpotify) as erro:
        cliente._executar(lambda: (_ for _ in ()).throw(SpotifyException(429, -1, "limite", headers={})))

    assert erro.value.status_http == 429


def test_api_demo_nao_exige_login() -> None:
    configuracao = Configuracao(spotify_modo="demo", spotify_url_frontend="http://frontend.test")
    contexto = ContextoSpotify(
        configuracao=configuracao,
        sessoes=ArmazenamentoSessoesSpotify(),
        cliente_real=ClienteSpotifyReal(configuracao),
        cliente_demo=ClienteSpotifyDemo(),
    )
    api = TestClient(criar_aplicacao(contexto))

    resposta = api.get("/api/spotify/top-faixas?usuario_demo=acustico")
    assert resposta.status_code == 200
    assert resposta.json()["fonte"] == "demo"
    assert api.get("/auth/spotify/iniciar", follow_redirects=False).status_code == 307


def test_catalogo_sem_csv_retorna_indisponivel(tmp_path) -> None:
    catalogo = CatalogoAtributos(tmp_path / "ausente.csv")
    assert catalogo.obter("qualquer") is None
