"""Shared matplotlib style constants and helpers for repo chart scripts."""

ACCENT = "#2a78d6"
INK = "#17150f"
INK_SECONDARY = "#5c584c"
GRID = "#e2dfd2"

TITLE_SIZE = 15
LABEL_SIZE = 12
TICK_SIZE = 10


def apply_style(ax) -> None:
    """Apply the shared chart look: clean spines, muted ticks/grid."""
    ax.set_facecolor("white")
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK_SECONDARY, labelsize=TICK_SIZE)
