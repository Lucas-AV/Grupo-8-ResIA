"""Builds dataset_profile.json, distribution PNGs, and a multi-genre-track
report from dataset.csv."""

import json

import matplotlib

matplotlib.use("Agg")  # headless: no display in CI, and no window needed locally

import matplotlib.pyplot as plt
import pandas as pd

from chart_style import ACCENT, GRID, INK, INK_SECONDARY, LABEL_SIZE, TITLE_SIZE, apply_style

INPUT_FILE = "dataset.csv"
PROFILE_FILE = "dataset_profile.json"
MULTI_GENRE_FILE = "dataset_multi_genre_tracks.csv"
ARTIST_OUTPUT_FILE = "artist_track_distribution.png"
ALBUM_OUTPUT_FILE = "album_track_distribution.png"

BUCKET_EDGES = [0, 1, 2, 3, 5, 10, 20, 1000]
BUCKET_LABELS = ["1", "2", "3", "4-5", "6-10", "11-20", "21+"]


def compute_profile(df: pd.DataFrame) -> dict:
    """Dataset-wide summary: row/uniqueness counts and null counts per column."""
    total_tracks = len(df)
    unique_track_ids = int(df["track_id"].nunique())
    null_counts = {col: int(n) for col, n in df.isna().sum().items() if n > 0}
    return {
        "total_tracks": total_tracks,
        "unique_track_ids": unique_track_ids,
        "duplicate_rows": total_tracks - unique_track_ids,
        "unique_artists": int(df["artists"].nunique()),
        "unique_albums": int(df["album_name"].nunique()),
        "unique_genres": int(df["track_genre"].nunique()),
        "null_counts": null_counts,
    }


def bucket_counts(group_sizes: pd.Series) -> pd.Series:
    """Bucket per-entity track counts into BUCKET_LABELS; counts entities per bucket."""
    buckets = pd.cut(group_sizes, bins=BUCKET_EDGES, labels=BUCKET_LABELS)
    return buckets.value_counts().reindex(BUCKET_LABELS, fill_value=0)


def top_multi_genre_tracks(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    """Tracks (by name+artist) that appear under more than one track_genre, most first."""
    grouped = (
        df.groupby(["track_name", "artists"])["track_genre"]
        .nunique()
        .reset_index(name="genre_count")
    )
    multi = grouped[grouped["genre_count"] > 1]
    return multi.sort_values("genre_count", ascending=False, kind="stable").head(n).reset_index(drop=True)


def plot_distribution(counts: pd.Series, title: str, ylabel: str, output_file: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)
    ax.bar(counts.index.astype(str), counts.values, color=ACCENT, width=0.6)

    max_value = max(counts.values.max(), 1)
    for i, value in enumerate(counts.values):
        ax.text(i, value + max_value * 0.015, str(int(value)), ha="center", fontsize=9, color=INK)

    ax.set_xlabel("Faixas na base", color=INK_SECONDARY, fontsize=LABEL_SIZE)
    ax.set_ylabel(ylabel, color=INK_SECONDARY, fontsize=LABEL_SIZE)
    ax.set_title(title, color=INK, fontsize=TITLE_SIZE, fontweight="bold", pad=14)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    apply_style(ax)

    fig.tight_layout()
    fig.savefig(output_file, facecolor="white")
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(INPUT_FILE)

    profile = compute_profile(df)
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    artist_counts = df.groupby("artists").size()
    plot_distribution(
        bucket_counts(artist_counts),
        "Artistas por quantidade de faixas na base",
        "Quantidade de artistas",
        ARTIST_OUTPUT_FILE,
    )

    album_counts = df.groupby("album_name").size()
    plot_distribution(
        bucket_counts(album_counts),
        "Albuns por quantidade de faixas na base",
        "Quantidade de albuns",
        ALBUM_OUTPUT_FILE,
    )

    top_multi_genre_tracks(df).to_csv(MULTI_GENRE_FILE, index=False)

    print(f"Gerado {PROFILE_FILE}, {ARTIST_OUTPUT_FILE}, {ALBUM_OUTPUT_FILE}, {MULTI_GENRE_FILE}.")


if __name__ == "__main__":
    main()
