"""Dados determinísticos para apresentação sem login ou credenciais Spotify."""

from __future__ import annotations

from datetime import UTC, datetime

from .modelos import (
    ArtistaSpotify,
    AtributosSpotify,
    ColetaSpotify,
    FaixaSpotify,
    PerfilSpotify,
    PeriodoSpotify,
)


def _atributos(**valores: float) -> AtributosSpotify:
    normalizados = {f"{chave}_norm": valor for chave, valor in valores.items()}
    return AtributosSpotify(**valores, **normalizados)


USUARIOS_DEMO: dict[str, dict[str, object]] = {
    "acustico": {
        "perfil": PerfilSpotify(id_pseudonimo="demo-acustico", nome_exibicao="Demo Acústico"),
        "artistas": [("a1", "Vozes do Cerrado", ["acoustic", "mpb"]), ("a2", "Luz Serena", ["folk"])],
        "faixas": [
            ("d-a1", "Manhã de Vidro", "Vozes do Cerrado", "Acústico", _atributos(danceability=.42, energy=.22, valence=.55, tempo=.78, acousticness=.91, instrumentalness=.01, speechiness=.04, liveness=.12, loudness=.44)),
            ("d-a2", "Perto do Sol", "Luz Serena", "Raízes", _atributos(danceability=.48, energy=.30, valence=.61, tempo=.63, acousticness=.82, instrumentalness=.02, speechiness=.03, liveness=.16, loudness=.49)),
        ],
    },
    "energetico": {
        "perfil": PerfilSpotify(id_pseudonimo="demo-energetico", nome_exibicao="Demo Energético"),
        "artistas": [("e1", "Pulso Norte", ["electronic", "dance"]), ("e2", "Linha Rápida", ["rock"])],
        "faixas": [
            ("d-e1", "Circuito Vivo", "Pulso Norte", "Frequência", _atributos(danceability=.81, energy=.92, valence=.72, tempo=.88, acousticness=.03, instrumentalness=.11, speechiness=.08, liveness=.18, loudness=.86)),
            ("d-e2", "Horizonte Alto", "Linha Rápida", "Impulso", _atributos(danceability=.66, energy=.86, valence=.64, tempo=.81, acousticness=.06, instrumentalness=.03, speechiness=.05, liveness=.21, loudness=.82)),
        ],
    },
    "ecletico": {
        "perfil": PerfilSpotify(id_pseudonimo="demo-ecletico", nome_exibicao="Demo Eclético"),
        "artistas": [("m1", "Mapa Aberto", ["jazz", "mpb"]), ("m2", "Cidade Neon", ["pop", "electronic"])],
        "faixas": [
            ("d-m1", "Entre Ruas", "Mapa Aberto", "Caminhos", _atributos(danceability=.57, energy=.48, valence=.45, tempo=.54, acousticness=.38, instrumentalness=.19, speechiness=.09, liveness=.28, loudness=.61)),
            ("d-m2", "Outra Direção", "Cidade Neon", "Luzes", _atributos(danceability=.74, energy=.68, valence=.77, tempo=.72, acousticness=.17, instrumentalness=.04, speechiness=.06, liveness=.14, loudness=.74)),
        ],
    },
}


class ClienteSpotifyDemo:
    def listar_usuarios(self) -> list[str]:
        return sorted(USUARIOS_DEMO)

    def coletar(self, usuario: str = "ecletico", periodo: PeriodoSpotify = "medium_term", limite: int = 20) -> ColetaSpotify:
        if usuario not in USUARIOS_DEMO:
            raise ValueError(f"Usuário demo desconhecido: {usuario}.")
        dados = USUARIOS_DEMO[usuario]
        faixas = [
            FaixaSpotify(
                posicao=posicao,
                track_id=track_id,
                nome=nome,
                artistas=[artista],
                album=album,
                atributos_audio=atributos,
                origem_atributos="demo",
            )
            for posicao, (track_id, nome, artista, album, atributos) in enumerate(dados["faixas"][:limite], start=1)
        ]
        artistas = [
            ArtistaSpotify(posicao=posicao, artista_id=artista_id, nome=nome, generos=generos)
            for posicao, (artista_id, nome, generos) in enumerate(dados["artistas"][:limite], start=1)
        ]
        return ColetaSpotify(
            fonte="demo",
            periodo=periodo,
            coletado_em=datetime.now(UTC),
            perfil=dados["perfil"],
            top_faixas=faixas,
            top_artistas=artistas,
            avisos=["Modo demo: dados fictícios para demonstração acadêmica."],
        )
