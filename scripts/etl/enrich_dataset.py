"""Build the recommendation dataset from the versioned raw Spotify sources.

The script preserves the public schema consumed by the project and writes
machine-readable hygiene reports alongside the resulting CSV.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
HYGIENE = ROOT / "data" / "hygiene"
OUTPUT = PROCESSED / "dataset.csv"

LOGICAL_COLUMNS = [
    "track_id", "artists", "album_name", "track_name", "popularity",
    "duration_ms", "explicit", "danceability", "energy", "key",
    "loudness", "mode", "speechiness", "acousticness",
    "instrumentalness", "liveness", "valence", "tempo",
    "time_signature", "track_genre",
]
FEATURES_01 = [
    "danceability", "energy", "speechiness", "acousticness",
    "instrumentalness", "liveness", "valence",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def slug(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def normalize_explicit(series: pd.Series) -> pd.Series:
    values = series.astype(str).str.strip().str.lower()
    mapping = {"true": True, "false": False, "1": True, "0": False}
    return values.map(mapping)


def normalize_frame(frame: pd.DataFrame, source: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return accepted rows and rejected rows without inventing missing values."""
    frame = frame.copy()
    frame = frame.drop(columns=["Unnamed: 0", "number", "index"], errors="ignore")
    if source == "top_10k_2025":
        frame = frame.rename(columns={"artist_names": "artists", "main_genres": "track_genre"})
        frame["artists"] = frame["artists"].astype(str).str.replace("|", ";", regex=False)
        frame["explicit"] = normalize_explicit(frame["explicit"])
        frame = frame.assign(track_genre=frame["track_genre"].fillna("").str.split(","))
        frame = frame.explode("track_genre", ignore_index=True)
        frame["track_genre"] = frame["track_genre"].map(slug)
    else:
        frame["explicit"] = normalize_explicit(frame["explicit"])
        frame["track_genre"] = frame["track_genre"].map(slug)

    missing_columns = sorted(set(LOGICAL_COLUMNS) - set(frame.columns))
    if missing_columns:
        raise ValueError(f"{source} is missing required columns: {missing_columns}")
    frame = frame[LOGICAL_COLUMNS].copy()
    for column in ["popularity", "duration_ms", "key", "loudness", "mode", "tempo", "time_signature", *FEATURES_01]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    invalid = pd.Series(False, index=frame.index)
    for column in ["track_id", "artists", "album_name", "track_name", "track_genre"]:
        invalid |= frame[column].isna() | frame[column].astype(str).str.strip().eq("")
    invalid |= frame["explicit"].isna()
    invalid |= frame["track_id"].astype(str).str.len().ne(22)
    invalid |= frame["popularity"].isna() | ~frame["popularity"].between(0, 100)
    invalid |= frame["duration_ms"].isna() | frame["duration_ms"].le(0)
    invalid |= frame["key"].isna() | ~frame["key"].between(-1, 11)
    invalid |= frame["mode"].isna() | ~frame["mode"].isin([0, 1])
    # A few valid Spotify records use 0 when tempo cannot be estimated.
    invalid |= frame["tempo"].isna() | frame["tempo"].lt(0)
    # Spotify uses 0/1 for a small number of tracks where the estimate is
    # unavailable or non-standard. They are valid source values and must not
    # cause existing rows to disappear.
    invalid |= frame["time_signature"].isna() | ~frame["time_signature"].between(0, 7)
    for column in FEATURES_01:
        invalid |= frame[column].isna() | ~frame[column].between(0, 1)

    rejected = frame.loc[invalid].assign(source=source, rejection_reason="missing_or_invalid_required_value")
    accepted = frame.loc[~invalid].copy()
    accepted["popularity"] = accepted["popularity"].astype(int)
    accepted["duration_ms"] = accepted["duration_ms"].astype(int)
    accepted["key"] = accepted["key"].astype(int)
    accepted["mode"] = accepted["mode"].astype(int)
    accepted["time_signature"] = accepted["time_signature"].astype(int)
    accepted["explicit"] = accepted["explicit"].astype(bool)
    return accepted, rejected


def load(name: str) -> pd.DataFrame:
    return pd.read_csv(RAW / name, low_memory=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    HYGIENE.mkdir(parents=True, exist_ok=True)

    current, current_rejected = normalize_frame(load("current_dataset_31819.csv"), "current")
    main_source, main_rejected = normalize_frame(load("spotify_tracks_114k.csv"), "spotify_tracks_114k")
    top, top_rejected = normalize_frame(load("spotify_top_10k_2025.csv"), "top_10k_2025")
    main_source.to_csv(PROCESSED / "spotify_tracks_114k_normalized.csv", index=False)
    top.to_csv(PROCESSED / "spotify_top_10k_2025_normalized.csv", index=False)

    ordered = pd.concat(
        [current.assign(_source="current"), main_source.assign(_source="spotify_tracks_114k"), top.assign(_source="top_10k_2025")],
        ignore_index=True,
    )
    duplicate_mask = ordered.duplicated(["track_id", "track_genre"], keep="first")
    dropped = ordered.loc[duplicate_mask, ["track_id", "track_genre", "_source"]].copy()
    merged = ordered.loc[~duplicate_mask, LOGICAL_COLUMNS].reset_index(drop=True)
    if merged["track_id"].nunique() <= main_source["track_id"].nunique():
        raise RuntimeError("The second source did not add a new track_id; output was not replaced.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(args.output, index=True)

    rejected = pd.concat([current_rejected, main_rejected, top_rejected], ignore_index=True)
    rejected.to_csv(HYGIENE / "rejected_rows.csv", index=False)
    report = {
        "deduplication_key": ["track_id", "track_genre"],
        "source_priority": ["current", "spotify_tracks_114k", "top_10k_2025"],
        "input_rows": {"current": len(current), "spotify_tracks_114k": len(main_source), "top_10k_2025": len(top)},
        "rejected_rows": int(len(rejected)),
        "exact_duplicate_rows_removed": int(duplicate_mask.sum()),
        "final_rows": int(len(merged)),
        "final_unique_track_ids": int(merged["track_id"].nunique()),
        "final_genres": int(merged["track_genre"].nunique()),
        "top_10k_new_track_ids": int(len(set(top["track_id"]) - set(main_source["track_id"]))),
        "dropped_by_source": dropped["_source"].value_counts().to_dict(),
    }
    (HYGIENE / "deduplication_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    schema = {
        "physical_columns": ["Unnamed: 0", *LOGICAL_COLUMNS],
        "logical_columns": LOGICAL_COLUMNS,
        "rows": int(len(merged)),
        "nulls": {column: int(value) for column, value in merged.isna().sum().items()},
        "types": {column: str(value) for column, value in merged.dtypes.items()},
    }
    (HYGIENE / "schema_report.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
    sources = [
        {"file": name, "sha256": sha256(RAW / name), "downloaded_on": str(date.today())}
        for name in ["current_dataset_31819.csv", "spotify_tracks_114k.csv", "spotify_top_10k_2025.csv"]
    ]
    (HYGIENE / "source_manifest.json").write_text(json.dumps({"sources": sources}, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
