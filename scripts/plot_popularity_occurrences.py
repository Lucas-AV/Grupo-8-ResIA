"""Gera popularity_occurrences.png a partir de dataset.csv.

Agrupa artistas por quantidade de ocorrencias (faixas) na tabela e mostra
a popularidade media de cada faixa de ocorrencia.
"""

import matplotlib

matplotlib.use("Agg")  # headless: no display in CI, and no window needed locally

import matplotlib.pyplot as plt
import pandas as pd

INPUT_FILE = "data/processed/dataset.csv"
OUTPUT_FILE = "images/popularity_occurrences.png"

ACCENT = "#2a78d6"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
GRID = "#e1e0d9"

BUCKET_EDGES = [0, 1, 2, 3, 5, 10, 20, 1000]
BUCKET_LABELS = ["1", "2", "3", "4-5", "6-10", "11-20", "21+"]


def style_axes(ax) -> None:
    ax.set_facecolor("white")
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.tick_params(colors=INK_SECONDARY, labelsize=9)


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    per_artist = df.groupby("artists")["popularity"].agg(["mean", "count"]).reset_index()
    per_artist["bucket"] = pd.cut(per_artist["count"], bins=BUCKET_EDGES, labels=BUCKET_LABELS)
    summary = per_artist.groupby("bucket", observed=True).agg(
        artistas=("mean", "size"), popularidade_media=("mean", "mean")
    )
    return summary.reindex(BUCKET_LABELS)


def plot_popularity_vs_occurrences(summary: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9, 6), dpi=150)
    bars = ax.bar(summary.index, summary["popularidade_media"], color=ACCENT, width=0.6)

    for bar, artistas in zip(bars, summary["artistas"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.6,
            f"n={artistas}",
            ha="center",
            fontsize=8,
            color=INK_SECONDARY,
        )

    ax.set_ylim(0, summary["popularidade_media"].max() * 1.2)
    ax.set_xlabel("Ocorrencias do artista na tabela (faixas)", color=INK_SECONDARY, fontsize=10)
    ax.set_ylabel("Popularidade media", color=INK_SECONDARY, fontsize=10)
    ax.set_title(
        "Popularidade media x quantidade de ocorrencias do artista",
        color=INK,
        fontsize=13,
        fontweight="bold",
        pad=14,
    )
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    style_axes(ax)

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, facecolor="white")
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(INPUT_FILE)
    summary = build_summary(df)
    plot_popularity_vs_occurrences(summary)
    print(f"Gerado {OUTPUT_FILE}.")


if __name__ == "__main__":
    main()
