"""Validate the dataset consumed by the analysis and recommendation pipeline."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
PROCESSED = DATA / "processed"
EXPECTED = ["Unnamed: 0", "track_id", "artists", "album_name", "track_name", "popularity", "duration_ms", "explicit", "danceability", "energy", "key", "loudness", "mode", "speechiness", "acousticness", "instrumentalness", "liveness", "valence", "tempo", "time_signature", "track_genre"]


def main() -> None:
    df = pd.read_csv(PROCESSED / "dataset.csv", low_memory=False)
    errors = []
    if list(df.columns) != EXPECTED:
        errors.append("physical_schema_mismatch")
    if df.drop(columns="Unnamed: 0").isna().any().any():
        errors.append("null_required_value")
    if df["Unnamed: 0"].tolist() != list(range(len(df))):
        errors.append("non_sequential_index")
    if df.duplicated(["track_id", "track_genre"]).any():
        errors.append("duplicate_track_genre")
    current = pd.read_csv(DATA / "raw" / "current_dataset_31819.csv", low_memory=False)
    current_keys = set(zip(current["track_id"], current["track_genre"]))
    final_keys = set(zip(df["track_id"], df["track_genre"]))
    if not current_keys.issubset(final_keys):
        errors.append("current_rows_not_preserved")
    report = {"status": "passed" if not errors else "failed", "errors": errors, "rows": len(df), "unique_track_ids": int(df.track_id.nunique()), "genres": int(df.track_genre.nunique())}
    (DATA / "hygiene" / "pipeline_validation.md").write_text("# Pipeline validation\n\n```json\n" + json.dumps(report, indent=2) + "\n```\n", encoding="utf-8")
    if errors:
        raise SystemExit(json.dumps(report))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
