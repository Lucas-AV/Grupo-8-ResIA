"""Gera precisao_cosseno.png a partir de data/analytics/precisao_cosseno.csv
(saida de avaliar_precisao_cosseno.py) — barras de precisao_media vs
baseline_aleatorio por valor de k."""

import matplotlib

matplotlib.use("Agg")  # headless: no display in CI, and no window needed locally

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from chart_style import ACCENT, GRID, INK, INK_SECONDARY, LABEL_SIZE, TITLE_SIZE, apply_style

INPUT_FILE = "data/analytics/precisao_cosseno.csv"
OUTPUT_FILE = "images/precisao_cosseno.png"

BASELINE_COLOR = "#c9c4b3"


def plot_precisao(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9, 6), dpi=150)

    posicoes = np.arange(len(df))
    largura = 0.35
    barras_precisao = ax.bar(
        posicoes - largura / 2, df["precisao_media"], largura, color=ACCENT, label="Precisao media (cosseno)"
    )
    ax.bar(
        posicoes + largura / 2,
        df["baseline_aleatorio"],
        largura,
        color=BASELINE_COLOR,
        label="Baseline aleatorio (mesmo genero por acaso)",
    )

    for barra, ganho in zip(barras_precisao, df["ganho_sobre_baseline"]):
        ax.text(
            barra.get_x() + barra.get_width() / 2,
            barra.get_height() + 0.003,
            f"{ganho:.1f}x",
            ha="center",
            fontsize=9,
            color=INK_SECONDARY,
        )

    ax.set_xticks(posicoes)
    ax.set_xticklabels([f"k={int(k)}" for k in df["k"]])
    ax.set_xlabel("Top-K vizinhos", color=INK_SECONDARY, fontsize=LABEL_SIZE)
    ax.set_ylabel("Precisao (proxy: mesmo track_genre)", color=INK_SECONDARY, fontsize=LABEL_SIZE)
    ax.set_title(
        "Precisao do motor de similaridade por cosseno vs. baseline aleatorio",
        color=INK,
        fontsize=TITLE_SIZE,
        fontweight="bold",
        pad=14,
    )
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK_SECONDARY)
    apply_style(ax)

    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, facecolor="white")
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(INPUT_FILE)
    plot_precisao(df)
    print(f"Gerado {OUTPUT_FILE}.")


if __name__ == "__main__":
    main()
