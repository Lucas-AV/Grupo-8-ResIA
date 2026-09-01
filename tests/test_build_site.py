import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "site"))

from build_site import load_genre_rows, load_profile_tiles, load_table_rows


def test_load_genre_rows_maps_and_rounds_columns(tmp_path):
    csv_path = tmp_path / "occurrences_by_genre.csv"
    csv_path.write_text(
        "track_genre,contagem,popularity,duration_ms,danceability,energy,key,"
        "loudness,mode,speechiness,acousticness,instrumentalness,liveness,"
        "valence,tempo,time_signature\n"
        "acoustic,1000,42.4834,214896.957,0.549593,0.435368,5.045,-9.447843,"
        "0.816,0.043247,0.566816,0.038336,0.153244,0.424023,119.010624,3.885\n",
        encoding="utf-8",
    )

    rows = load_genre_rows(csv_path)

    assert rows == [
        {
            "g": "acoustic",
            "n": 1000,
            "pop": 42.5,
            "dance": 0.55,
            "energy": 0.435,
            "tempo": 119.0,
            "valence": 0.424,
            "acoustic": 0.567,
        }
    ]


def test_load_genre_rows_preserves_csv_row_order(tmp_path):
    csv_path = tmp_path / "occurrences_by_genre.csv"
    csv_path.write_text(
        "track_genre,contagem,popularity,duration_ms,danceability,energy,key,"
        "loudness,mode,speechiness,acousticness,instrumentalness,liveness,"
        "valence,tempo,time_signature\n"
        "b-genre,10,20,200000,0.5,0.5,5,-6,0.5,0.1,0.1,0.1,0.1,0.5,120,4\n"
        "a-genre,20,30,200000,0.5,0.5,5,-6,0.5,0.1,0.1,0.1,0.1,0.5,120,4\n",
        encoding="utf-8",
    )

    rows = load_genre_rows(csv_path)

    assert [row["g"] for row in rows] == ["b-genre", "a-genre"]


def test_load_profile_tiles_formats_counts_and_duplicate_sub(tmp_path):
    profile_path = tmp_path / "dataset_profile.json"
    profile_path.write_text(
        json.dumps(
            {
                "total_tracks": 31819,
                "unique_track_ids": 28888,
                "duplicate_rows": 2931,
                "unique_artists": 10872,
                "unique_albums": 15481,
                "unique_genres": 32,
                "null_counts": {},
            }
        ),
        encoding="utf-8",
    )

    tiles = load_profile_tiles(profile_path)

    assert tiles == [
        {"label": "Faixas na base", "value": "31.819"},
        {
            "label": "Faixas unicas",
            "value": "28.888",
            "sub": "2931 linhas duplicadas (mesma faixa em outro genero)",
        },
        {"label": "Artistas", "value": "10.872"},
        {"label": "Albuns", "value": "15.481"},
        {"label": "Generos", "value": "32"},
        {"label": "Valores nulos", "value": "0"},
    ]


def test_load_profile_tiles_sums_null_counts_across_columns(tmp_path):
    profile_path = tmp_path / "dataset_profile.json"
    profile_path.write_text(
        json.dumps(
            {
                "total_tracks": 2,
                "unique_track_ids": 2,
                "duplicate_rows": 0,
                "unique_artists": 2,
                "unique_albums": 2,
                "unique_genres": 1,
                "null_counts": {"artists": 1, "album_name": 2},
            }
        ),
        encoding="utf-8",
    )

    tiles = load_profile_tiles(profile_path)

    nulls_tile = next(tile for tile in tiles if tile["label"] == "Valores nulos")
    assert nulls_tile["value"] == "3"


def test_load_table_rows_selects_columns_and_preserves_order(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text(
        "track_name,artists,genre_count,extra\n"
        "Song A,Artist X,3,ignored\n"
        "Song B,Artist Y,2,ignored\n",
        encoding="utf-8",
    )

    rows = load_table_rows(csv_path, ["track_name", "artists", "genre_count"])

    assert rows == [
        ["Song A", "Artist X", 3],
        ["Song B", "Artist Y", 2],
    ]
