"""Gera correlation_heatmap.png e correlations_top_pairs.csv a partir de
dataset.csv."""

import matplotlib

matplotlib.use("Agg")  # headless: no display in CI, and no window needed locally

import matplotlib.pyplot as plt
import pandas as pd

from chart_style import INK, INK_SECONDARY, TICK_SIZE, TITLE_SIZE

INPUT_FILE = "data/dataset.csv"
HEATMAP_FILE = "images/correlation_heatmap.png"
TOP_PAIRS_FILE = "data/correlations_top_pairs.csv"

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
    """Pares de maior correlacao (em modulo), sem auto-pares nem duplicatas simetricas."""
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


def plot_heatmap(corr: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9, 8), dpi=150)
    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)

    columns = list(corr.columns)
    ax.set_xticks(range(len(columns)))
    ax.set_yticks(range(len(columns)))
    ax.set_xticklabels(columns, rotation=45, ha="right", fontsize=TICK_SIZE, color=INK_SECONDARY)
    ax.set_yticklabels(columns, fontsize=TICK_SIZE, color=INK_SECONDARY)

    for i in range(len(columns)):
        for j in range(len(columns)):
            value = corr.values[i, j]
            text_color = "white" if abs(value) > 0.6 else INK
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=8, color=text_color)

    ax.set_title(
        "Correlacao entre popularidade, duracao e features de audio",
        color=INK,
        fontsize=TITLE_SIZE,
        fontweight="bold",
        pad=14,
    )
    fig.colorbar(im, ax=ax, shrink=0.8, label="Correlacao (Pearson)")
    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.tight_layout()
    fig.savefig(HEATMAP_FILE, facecolor="white")
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(INPUT_FILE)
    corr = compute_correlation_matrix(df)
    plot_heatmap(corr)
    top_pairs(corr).to_csv(TOP_PAIRS_FILE, index=False)
    print(f"Gerado {HEATMAP_FILE} e {TOP_PAIRS_FILE}.")


if __name__ == "__main__":
    main()
