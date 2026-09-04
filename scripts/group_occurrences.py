"""Agrupa dataset.csv por coluna e conta ocorrencias de cada valor.

Gera um CSV de saida no formato longo: coluna, valor, contagem.
Gera tambem um CSV com o agrupamento focado em track_genre
(contagem de faixas + medias das colunas numericas por genero).
"""

import pandas as pd

INPUT_FILE = "data/processed/dataset.csv"
OUTPUT_FILE = "data/analytics/occurrences_by_column.csv"
GENRE_COLUMN = "track_genre"
GENRE_OUTPUT_FILE = "data/analytics/occurrences_by_genre.csv"


def build_occurrence_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column in df.columns:
        # Skip the index column from CSV
        if column == "Unnamed: 0":
            continue
        counts = (
            df[column]
            .value_counts(dropna=False)
            .sort_index()
            .sort_values(ascending=False, kind="stable")
        )
        for value, count in counts.items():
            rows.append({"coluna": column, "valor": value, "contagem": count})
    result = pd.DataFrame(rows)
    return result.sort_values(
        ["coluna", "contagem"], ascending=[True, False], kind="stable"
    )


def build_genre_summary(df: pd.DataFrame) -> pd.DataFrame:
    numeric_columns = df.select_dtypes(include="number").columns.drop(
        "Unnamed: 0", errors="ignore"
    )
    summary = df.groupby(GENRE_COLUMN)[numeric_columns].mean(numeric_only=True)
    summary.insert(0, "contagem", df.groupby(GENRE_COLUMN).size())
    summary = summary.sort_values("contagem", ascending=False, kind="stable").reset_index()
    return summary


def main() -> None:
    df = pd.read_csv(INPUT_FILE)

    occurrences = build_occurrence_table(df)
    occurrences.to_csv(OUTPUT_FILE, index=False)
    print(f"Gerado {OUTPUT_FILE} com {len(occurrences)} linhas.")

    genre_summary = build_genre_summary(df)
    genre_summary.to_csv(GENRE_OUTPUT_FILE, index=False)
    print(f"Gerado {GENRE_OUTPUT_FILE} com {len(genre_summary)} linhas.")


if __name__ == "__main__":
    main()
