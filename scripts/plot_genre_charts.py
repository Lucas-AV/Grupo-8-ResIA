"""Gera graficos (PNG) a partir de occurrences_by_genre.csv.

Produz:
  - genre_popularity.png: barras horizontais, popularidade media por genero.
  - genre_energy_dance.png: dispersao energia x dancabilidade por genero.
"""

import matplotlib

matplotlib.use("Agg")  # headless: no display in CI, and no window needed locally

import matplotlib.pyplot as plt
import pandas as pd
from adjustText import adjust_text

from chart_style import (
    ACCENT,
    GRID,
    INK,
    INK_SECONDARY,
    LABEL_SIZE,
    TICK_SIZE,
    TITLE_SIZE,
    apply_style,
)

INPUT_FILE = "data/occurrences_by_genre.csv"
BAR_OUTPUT_FILE = "images/genre_popularity.png"
SCATTER_OUTPUT_FILE = "images/genre_energy_dance.png"


def plot_popularity_bars(df: pd.DataFrame) -> None:
    ranked = df.sort_values("popularity", ascending=True)

    fig, ax = plt.subplots(figsize=(9, 11), dpi=150)
    bars = ax.barh(ranked["track_genre"], ranked["popularity"], color=ACCENT, height=0.7)

    for bar, value in zip(bars, ranked["popularity"]):
        ax.text(
            bar.get_width() + 0.6,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.1f}",
            va="center",
            fontsize=TICK_SIZE,
            color=INK,
        )

    ax.set_xlim(0, ranked["popularity"].max() * 1.15)
    ax.set_xlabel("Popularidade media", color=INK_SECONDARY, fontsize=LABEL_SIZE)
    ax.set_title("Popularidade media por genero", color=INK, fontsize=TITLE_SIZE, fontweight="bold", pad=14)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    apply_style(ax)

    fig.tight_layout()
    fig.savefig(BAR_OUTPUT_FILE, facecolor="white")
    plt.close(fig)


def plot_energy_vs_dance(df: pd.DataFrame) -> None:
    # Figure is larger than the bar chart's: 32 genres cluster tightly in
    # danceability/energy space, and adjust_text needs real pixel room to
    # separate labels without any two overlapping.
    fig, ax = plt.subplots(figsize=(13, 13), dpi=150)
    ax.scatter(
        df["danceability"],
        df["energy"],
        s=70,
        color=ACCENT,
        alpha=0.85,
        edgecolors="white",
        linewidths=1,
        zorder=3,
    )

    texts = [
        ax.text(
            row["danceability"],
            row["energy"],
            row["track_genre"],
            fontsize=TICK_SIZE - 1,
            color=INK_SECONDARY,
        )
        for _, row in df.iterrows()
    ]
    adjust_text(
        texts,
        x=df["danceability"].to_numpy(),
        y=df["energy"].to_numpy(),
        ax=ax,
        # Defaults (max_move=(10, 10), force_text=(0.1, 0.2)) barely move
        # labels and leave the dense central cluster overlapping; these are
        # tuned so every one of the 32 genre labels clears both its
        # neighbors' labels and other points.
        expand=(1.4, 1.7),
        force_text=(1.2, 1.6),
        force_static=(0.5, 0.7),
        max_move=(400, 400),
        time_lim=25,
        arrowprops=dict(arrowstyle="-", color=INK_SECONDARY, lw=0.6),
    )

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Dancabilidade", color=INK_SECONDARY, fontsize=LABEL_SIZE)
    ax.set_ylabel("Energia", color=INK_SECONDARY, fontsize=LABEL_SIZE)
    ax.set_title("Energia x Dancabilidade por genero", color=INK, fontsize=TITLE_SIZE, fontweight="bold", pad=14)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    apply_style(ax)

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
