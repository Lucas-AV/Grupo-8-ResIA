import pandas as pd

from plot_correlations import compute_correlation_matrix, top_pairs


def test_compute_correlation_matrix_selects_given_columns():
    df = pd.DataFrame(
        {
            "a": [1, 2, 3, 4],
            "b": [4, 3, 2, 1],
            "c": [1, 1, 1, 1],
            "unused": [9, 9, 9, 9],
        }
    )
    corr = compute_correlation_matrix(df, columns=["a", "b", "c"])
    assert list(corr.columns) == ["a", "b", "c"]
    assert corr.loc["a", "b"] == -1.0


def test_top_pairs_excludes_self_and_duplicate_pairs():
    corr = pd.DataFrame(
        {
            "a": [1.0, 0.9, 0.1],
            "b": [0.9, 1.0, -0.8],
            "c": [0.1, -0.8, 1.0],
        },
        index=["a", "b", "c"],
    )
    result = top_pairs(corr, n=10)
    assert len(result) == 3
    assert set(zip(result["column_a"], result["column_b"])) == {("a", "b"), ("a", "c"), ("b", "c")}


def test_top_pairs_orders_by_absolute_value_and_respects_n():
    corr = pd.DataFrame(
        {
            "a": [1.0, 0.9, 0.1],
            "b": [0.9, 1.0, -0.8],
            "c": [0.1, -0.8, 1.0],
        },
        index=["a", "b", "c"],
    )
    result = top_pairs(corr, n=2)
    assert len(result) == 2
    assert result.iloc[0]["column_a"] == "a"
    assert result.iloc[0]["column_b"] == "b"
    assert result.iloc[1]["column_a"] == "b"
    assert result.iloc[1]["column_b"] == "c"
