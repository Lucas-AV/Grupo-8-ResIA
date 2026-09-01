from backend.utilitarios.catalogo import faixa_do_kaggle


def test_converte_linha_kaggle_para_contrato() -> None:
    faixa = faixa_do_kaggle(
        {
            "track_id": "1",
            "track_name": "Faixa",
            "artists": "Artista A; Artista B",
            "album_name": "Álbum",
            "track_genre": "alt-rock",
            "popularity": 40,
            "danceability": 0.6,
            "energy": 0.7,
        }
    )

    assert faixa is not None
    assert faixa.fonte == "kaggle-spotify-tracks"
    assert faixa.artistas == ["Artista A", "Artista B"]
    assert faixa.generos == ["alt rock"]


def test_rejeita_linha_sem_identificador() -> None:
    assert faixa_do_kaggle({"track_name": "Sem ID"}) is None

