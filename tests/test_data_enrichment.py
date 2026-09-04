import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def test_enriched_dataset_preserves_schema_and_current_rows():
    dataset = pd.read_csv(ROOT / "data" / "processed" / "dataset.csv")
    current = pd.read_csv(ROOT / "data" / "raw" / "current_dataset_31819.csv")
    assert list(dataset.columns)[0] == "Unnamed: 0"
    assert len(dataset) > 114_000
    assert dataset.track_id.nunique() > 89_741
    assert not dataset.drop(columns="Unnamed: 0").isna().any().any()
    assert not dataset.duplicated(["track_id", "track_genre"]).any()
    assert set(zip(current.track_id, current.track_genre)).issubset(set(zip(dataset.track_id, dataset.track_genre)))


def test_hygiene_reports_successful_multibase_merge():
    report = json.loads((ROOT / "data" / "hygiene" / "deduplication_report.json").read_text(encoding="utf-8"))
    assert report["top_10k_new_track_ids"] > 0
    assert report["final_unique_track_ids"] > 89_741
