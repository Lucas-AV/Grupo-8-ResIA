import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "site"))

from build_site import load_genre_rows


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
