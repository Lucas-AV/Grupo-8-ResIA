import pandas as pd

from profile_dataset import BUCKET_LABELS, bucket_counts, compute_profile, top_multi_genre_tracks


def test_compute_profile_counts_uniques_and_duplicates():
    df = pd.DataFrame(
        {
            "track_id": ["a", "a", "b"],
            "artists": ["X", "X", "Y"],
            "album_name": ["Alb1", "Alb1", "Alb2"],
            "track_genre": ["pop", "rock", "pop"],
        }
    )
    profile = compute_profile(df)
    assert profile == {
        "total_tracks": 3,
        "unique_track_ids": 2,
        "duplicate_rows": 1,
        "unique_artists": 2,
        "unique_albums": 2,
        "unique_genres": 2,
        "null_counts": {},
    }


def test_compute_profile_reports_null_counts():
    df = pd.DataFrame(
        {
            "track_id": ["a", "b"],
            "artists": ["X", None],
            "album_name": ["Alb1", "Alb2"],
            "track_genre": ["pop", "rock"],
        }
    )
    profile = compute_profile(df)
    assert profile["null_counts"] == {"artists": 1}


def test_bucket_counts_places_entities_in_correct_buckets():
    sizes = pd.Series([1, 1, 2, 4, 25])
    counts = bucket_counts(sizes)
    assert counts["1"] == 2
    assert counts["2"] == 1
    assert counts["4-5"] == 1
    assert counts["21+"] == 1
    assert counts["3"] == 0


def test_bucket_counts_returns_all_labels_in_order():
    sizes = pd.Series([1])
    counts = bucket_counts(sizes)
    assert list(counts.index) == BUCKET_LABELS


def test_top_multi_genre_tracks_filters_and_sorts():
    df = pd.DataFrame(
        {
            "track_name": ["Song A", "Song A", "Song A", "Song B", "Song C"],
            "artists": ["X", "X", "X", "Y", "Z"],
            "track_genre": ["pop", "rock", "indie", "pop", "pop"],
        }
    )
    result = top_multi_genre_tracks(df, n=15)
    assert list(result["track_name"]) == ["Song A"]
    assert result.iloc[0]["genre_count"] == 3


def test_top_multi_genre_tracks_respects_n():
    df = pd.DataFrame(
        {
            "track_name": ["A", "A", "B", "B", "C", "C"],
            "artists": ["x", "x", "y", "y", "z", "z"],
            "track_genre": ["g1", "g2", "g1", "g2", "g1", "g2"],
        }
    )
    result = top_multi_genre_tracks(df, n=2)
    assert len(result) == 2
