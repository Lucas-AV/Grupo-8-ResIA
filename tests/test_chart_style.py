import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from chart_style import GRID, apply_style


def test_apply_style_hides_top_right_left_spines():
    fig, ax = plt.subplots()
    apply_style(ax)
    assert ax.spines["top"].get_visible() is False
    assert ax.spines["right"].get_visible() is False
    assert ax.spines["left"].get_visible() is False
    plt.close(fig)


def test_apply_style_colors_bottom_spine_with_grid_color():
    fig, ax = plt.subplots()
    apply_style(ax)
    assert ax.spines["bottom"].get_edgecolor() == matplotlib.colors.to_rgba(GRID)
    plt.close(fig)
