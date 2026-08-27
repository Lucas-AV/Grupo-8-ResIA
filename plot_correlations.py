"""Builds correlation_heatmap.png and correlations_top_pairs.csv from
dataset.csv."""

import matplotlib

matplotlib.use("Agg")  # headless: no display in CI, and no window needed locally

import matplotlib.pyplot as plt
import pandas as pd

from chart_style import INK, INK_SECONDARY, TICK_SIZE, TITLE_SIZE

INPUT_FILE = "dataset.csv"
HEATMAP_FILE = "correlation_heatmap.png"
TOP_PAIRS_FILE = "correlations_top_pairs.csv"

CORRELATION_COLUMNS = [
    "popularity",
    "duration_ms",
    "danceability",
    "energy",
    "loudness",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
]


def compute_correlation_matrix(df: pd.DataFrame, columns: list[str] = CORRELATION_COLUMNS) -> pd.DataFrame:
    return df[columns].corr()


def top_pairs(corr: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Largest-magnitude correlation pairs, self-pairs and symmetric duplicates removed."""
    columns = list(corr.columns)
    rows = [
        {"column_a": col_a, "column_b": col_b, "correlation": corr.loc[col_a, col_b]}
        for i, col_a in enumerate(columns)
        for col_b in columns[i + 1 :]
    ]
    result = pd.DataFrame(rows)
    result["abs_correlation"] = result["correlation"].abs()
    result = result.sort_values("abs_correlation", ascending=False, kind="stable").drop(columns="abs_correlation")
    return result.head(n).reset_index(drop=True)
