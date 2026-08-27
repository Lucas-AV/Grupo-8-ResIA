"""Gera genre_mode.png: proporcao de mode (escala) por genero.

mode 1 = escala maior (alta); mode 0 = escala menor (baixa).
"""

import matplotlib.pyplot as plt
import pandas as pd

INPUT_FILE = "dataset.csv"
OUTPUT_FILE = "genre_mode.png"

MODE1_COLOR = "#2a78d6"  # escala alta
MODE0_COLOR = "#eb6834"  # escala baixa
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
GRID = "#e1e0d9"


def style_axes(ax) -> None:
    ax.set_facecolor("white")
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK_SECONDARY, labelsize=9)


def plot_genre_mode(df: pd.DataFrame) -> None:
    share = df.groupby("track_genre")["mode"].mean().sort_values()
    genres = share.index
    mode1_pct = share.values * 100
    mode0_pct = 100 - mode1_pct

    fig, ax = plt.subplots(figsize=(8, 10), dpi=150)
    ax.barh(genres, mode0_pct, color=MODE0_COLOR, height=0.7, label="Escala baixa (mode 0)")
    ax.barh(genres, mode1_pct, left=mode0_pct, color=MODE1_COLOR, height=0.7, label="Escala alta (mode 1)")

    ax.set_xlim(0, 100)
    ax.set_xlabel("Proporcao de faixas (%)", color=INK_SECONDARY, fontsize=10)
    ax.set_title("Escala (mode) por genero", color=INK, fontsize=13, fontweight="bold", pad=14)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    style_axes(ax)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.06), ncol=2, frameon=False, fontsize=9)

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(INPUT_FILE)
    plot_genre_mode(df)
    print(f"Gerado {OUTPUT_FILE}.")


if __name__ == "__main__":
    main()
