"""Gera graficos (PNG) a partir de occurrences_by_genre.csv.

Produz:
  - genre_popularity.png: barras horizontais, popularidade media por genero.
  - genre_energy_dance.png: dispersao energia x dancabilidade por genero.
"""

import matplotlib.pyplot as plt
import pandas as pd

INPUT_FILE = "occurrences_by_genre.csv"
BAR_OUTPUT_FILE = "genre_popularity.png"
SCATTER_OUTPUT_FILE = "genre_energy_dance.png"

ACCENT = "#2a78d6"
INK = "#17150f"
INK_SECONDARY = "#5c584c"
GRID = "#e2dfd2"


def style_axes(ax) -> None:
    ax.set_facecolor("white")
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK_SECONDARY, labelsize=9)


def plot_popularity_bars(df: pd.DataFrame) -> None:
    ranked = df.sort_values("popularity", ascending=True)

    fig, ax = plt.subplots(figsize=(8, 10), dpi=150)
    bars = ax.barh(ranked["track_genre"], ranked["popularity"], color=ACCENT, height=0.7)

    for bar, value in zip(bars, ranked["popularity"]):
        ax.text(
            bar.get_width() + 0.6,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.1f}",
            va="center",
            fontsize=8,
            color=INK,
        )

    ax.set_xlim(0, ranked["popularity"].max() * 1.15)
    ax.set_xlabel("Popularidade media", color=INK_SECONDARY, fontsize=10)
    ax.set_title("Popularidade media por genero", color=INK, fontsize=13, fontweight="bold", pad=14)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    style_axes(ax)

    fig.tight_layout()
    fig.savefig(BAR_OUTPUT_FILE, facecolor="white")
    plt.close(fig)


def plot_energy_vs_dance(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 8), dpi=150)
    ax.scatter(df["danceability"], df["energy"], s=60, color=ACCENT, alpha=0.8, edgecolors="white", linewidths=1)

    for _, row in df.iterrows():
        ax.annotate(
            row["track_genre"],
            (row["danceability"], row["energy"]),
            fontsize=6.5,
            color=INK_SECONDARY,
            xytext=(4, 3),
            textcoords="offset points",
        )

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Dancabilidade", color=INK_SECONDARY, fontsize=10)
    ax.set_ylabel("Energia", color=INK_SECONDARY, fontsize=10)
    ax.set_title("Energia x Dancabilidade por genero", color=INK, fontsize=13, fontweight="bold", pad=14)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    style_axes(ax)

    fig.tight_layout()
    fig.savefig(SCATTER_OUTPUT_FILE, facecolor="white")
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(INPUT_FILE)
    plot_popularity_bars(df)
    plot_energy_vs_dance(df)
    print(f"Gerado {BAR_OUTPUT_FILE} e {SCATTER_OUTPUT_FILE}.")


if __name__ == "__main__":
    main()
