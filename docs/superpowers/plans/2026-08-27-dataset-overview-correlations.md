# Dataset Overview and Correlation Analyses Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two new GitHub Pages analyses — a dataset-wide overview (row/artist/album/genre counts, duplicates, null check, distributions) and a correlation study (popularity, duration, and 9 audio features) — fed by two new root scripts, following the existing script-produces-CSV/PNG → `build_site.py`-renders-templates pipeline.

**Architecture:** `profile_dataset.py` and `plot_correlations.py` join `group_occurrences.py`/`plot_genre_charts.py` at the repo root, each with testable pure functions plus a `main()` that writes CSV/JSON/PNG outputs. `site/templates/analise.html` is generalized from a single-image template to one that accepts optional `tiles`, a list of `figures`, and an optional `table`, so it serves both the new data-heavy pages and the two existing static pages (`modo.html`, `popularidade.html`), which get migrated to the same shape.

**Tech Stack:** Python 3, pandas, matplotlib (Agg backend), Jinja2, pytest — no new dependencies.

Reference spec: `docs/superpowers/specs/2026-08-27-dataset-overview-correlations-design.md`

---

### Task 1: `profile_dataset.py` — pure functions (TDD)

**Files:**
- Create: `profile_dataset.py` (functions only in this task; script wiring in Task 2)
- Test: `tests/test_profile_dataset.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_profile_dataset.py`:

```python
import pandas as pd

from profile_dataset import BUCKET_LABELS, bucket_counts, compute_profile, top_multi_genre_tracks


def test_compute_profile_counts_uniques_and_duplicates():
    df = pd.DataFrame(
        {
            "track_id": ["a", "a", "b"],
            "artists": ["X", "X", "Y"],
            "album_name": ["Alb1", "Alb1", "Alb2"],
            "track_genre": ["pop", "rock", "pop"],
        }
    )
    profile = compute_profile(df)
    assert profile == {
        "total_tracks": 3,
        "unique_track_ids": 2,
        "duplicate_rows": 1,
        "unique_artists": 2,
        "unique_albums": 2,
        "unique_genres": 2,
        "null_counts": {},
    }


def test_compute_profile_reports_null_counts():
    df = pd.DataFrame(
        {
            "track_id": ["a", "b"],
            "artists": ["X", None],
            "album_name": ["Alb1", "Alb2"],
            "track_genre": ["pop", "rock"],
        }
    )
    profile = compute_profile(df)
    assert profile["null_counts"] == {"artists": 1}


def test_bucket_counts_places_entities_in_correct_buckets():
    sizes = pd.Series([1, 1, 2, 4, 25])
    counts = bucket_counts(sizes)
    assert counts["1"] == 2
    assert counts["2"] == 1
    assert counts["4-5"] == 1
    assert counts["21+"] == 1
    assert counts["3"] == 0


def test_bucket_counts_returns_all_labels_in_order():
    sizes = pd.Series([1])
    counts = bucket_counts(sizes)
    assert list(counts.index) == BUCKET_LABELS


def test_top_multi_genre_tracks_filters_and_sorts():
    df = pd.DataFrame(
        {
            "track_name": ["Song A", "Song A", "Song A", "Song B", "Song C"],
            "artists": ["X", "X", "X", "Y", "Z"],
            "track_genre": ["pop", "rock", "indie", "pop", "pop"],
        }
    )
    result = top_multi_genre_tracks(df, n=15)
    assert list(result["track_name"]) == ["Song A"]
    assert result.iloc[0]["genre_count"] == 3


def test_top_multi_genre_tracks_respects_n():
    df = pd.DataFrame(
        {
            "track_name": ["A", "A", "B", "B", "C", "C"],
            "artists": ["x", "x", "y", "y", "z", "z"],
            "track_genre": ["g1", "g2", "g1", "g2", "g1", "g2"],
        }
    )
    result = top_multi_genre_tracks(df, n=2)
    assert len(result) == 2
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `source .venv/Scripts/activate && python -m pytest tests/test_profile_dataset.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'profile_dataset'`

- [ ] **Step 3: Write `profile_dataset.py` with just the functions**

```python
"""Builds dataset_profile.json, distribution PNGs, and a multi-genre-track
report from dataset.csv."""

import json

import matplotlib

matplotlib.use("Agg")  # headless: no display in CI, and no window needed locally

import matplotlib.pyplot as plt
import pandas as pd

from chart_style import ACCENT, GRID, INK, INK_SECONDARY, LABEL_SIZE, TITLE_SIZE, apply_style

INPUT_FILE = "dataset.csv"
PROFILE_FILE = "dataset_profile.json"
MULTI_GENRE_FILE = "dataset_multi_genre_tracks.csv"
ARTIST_OUTPUT_FILE = "artist_track_distribution.png"
ALBUM_OUTPUT_FILE = "album_track_distribution.png"

BUCKET_EDGES = [0, 1, 2, 3, 5, 10, 20, 1000]
BUCKET_LABELS = ["1", "2", "3", "4-5", "6-10", "11-20", "21+"]


def compute_profile(df: pd.DataFrame) -> dict:
    """Dataset-wide summary: row/uniqueness counts and null counts per column."""
    total_tracks = len(df)
    unique_track_ids = int(df["track_id"].nunique())
    null_counts = {col: int(n) for col, n in df.isna().sum().items() if n > 0}
    return {
        "total_tracks": total_tracks,
        "unique_track_ids": unique_track_ids,
        "duplicate_rows": total_tracks - unique_track_ids,
        "unique_artists": int(df["artists"].nunique()),
        "unique_albums": int(df["album_name"].nunique()),
        "unique_genres": int(df["track_genre"].nunique()),
        "null_counts": null_counts,
    }


def bucket_counts(group_sizes: pd.Series) -> pd.Series:
    """Bucket per-entity track counts into BUCKET_LABELS; counts entities per bucket."""
    buckets = pd.cut(group_sizes, bins=BUCKET_EDGES, labels=BUCKET_LABELS)
    return buckets.value_counts().reindex(BUCKET_LABELS, fill_value=0)


def top_multi_genre_tracks(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    """Tracks (by name+artist) that appear under more than one track_genre, most first."""
    grouped = (
        df.groupby(["track_name", "artists"])["track_genre"]
        .nunique()
        .reset_index(name="genre_count")
    )
    multi = grouped[grouped["genre_count"] > 1]
    return multi.sort_values("genre_count", ascending=False).head(n).reset_index(drop=True)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `source .venv/Scripts/activate && python -m pytest tests/test_profile_dataset.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add profile_dataset.py tests/test_profile_dataset.py
git commit -m "$(cat <<'EOF'
Add dataset profile pure functions

compute_profile(), bucket_counts(), and top_multi_genre_tracks() are
the testable core of the upcoming dataset-overview analysis: row and
uniqueness counts, per-entity track-count bucketing, and the tracks
that show up under more than one genre.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: `profile_dataset.py` — wire up the full script

**Files:**
- Modify: `profile_dataset.py`

- [ ] **Step 1: Add plotting and `main()` to `profile_dataset.py`**

Append to the end of `profile_dataset.py` (after `top_multi_genre_tracks`):

```python


def plot_distribution(counts: pd.Series, title: str, ylabel: str, output_file: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)
    ax.bar(counts.index.astype(str), counts.values, color=ACCENT, width=0.6)

    max_value = max(counts.values.max(), 1)
    for i, value in enumerate(counts.values):
        ax.text(i, value + max_value * 0.015, str(int(value)), ha="center", fontsize=9, color=INK)

    ax.set_xlabel("Faixas na base", color=INK_SECONDARY, fontsize=LABEL_SIZE)
    ax.set_ylabel(ylabel, color=INK_SECONDARY, fontsize=LABEL_SIZE)
    ax.set_title(title, color=INK, fontsize=TITLE_SIZE, fontweight="bold", pad=14)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    apply_style(ax)

    fig.tight_layout()
    fig.savefig(output_file, facecolor="white")
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(INPUT_FILE)

    profile = compute_profile(df)
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    artist_counts = df.groupby("artists").size()
    plot_distribution(
        bucket_counts(artist_counts),
        "Artistas por quantidade de faixas na base",
        "Quantidade de artistas",
        ARTIST_OUTPUT_FILE,
    )

    album_counts = df.groupby("album_name").size()
    plot_distribution(
        bucket_counts(album_counts),
        "Albuns por quantidade de faixas na base",
        "Quantidade de albuns",
        ALBUM_OUTPUT_FILE,
    )

    top_multi_genre_tracks(df).to_csv(MULTI_GENRE_FILE, index=False)

    print(f"Gerado {PROFILE_FILE}, {ARTIST_OUTPUT_FILE}, {ALBUM_OUTPUT_FILE}, {MULTI_GENRE_FILE}.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it and inspect the output**

Run: `source .venv/Scripts/activate && python profile_dataset.py`
Expected: `Gerado dataset_profile.json, artist_track_distribution.png, album_track_distribution.png, dataset_multi_genre_tracks.csv.`

Check the JSON is sane:
Run: `cat dataset_profile.json`
Expected: `total_tracks` around 31819, `duplicate_rows` around 2931, no exceptions.

Open both PNGs (Read tool or OS viewer) and confirm: 7 bars each (`1, 2, 3, 4-5, 6-10, 11-20, 21+`), value labels readable, title/axis text crisp.

- [ ] **Step 3: Run the existing test suite to confirm nothing broke**

Run: `source .venv/Scripts/activate && python -m pytest tests/ -v`
Expected: all tests pass (profile_dataset + build_site + chart_style).

- [ ] **Step 4: Commit**

```bash
git add profile_dataset.py dataset_profile.json artist_track_distribution.png album_track_distribution.png dataset_multi_genre_tracks.csv
git commit -m "$(cat <<'EOF'
Generate dataset overview outputs

profile_dataset.py now writes dataset_profile.json, the two
artist/album track-count distribution PNGs, and the multi-genre
tracks CSV that the site's upcoming visao-geral.html page will read.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: `plot_correlations.py` — pure functions (TDD)

**Files:**
- Create: `plot_correlations.py` (functions only in this task; script wiring in Task 4)
- Test: `tests/test_correlations.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_correlations.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `source .venv/Scripts/activate && python -m pytest tests/test_correlations.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'plot_correlations'`

- [ ] **Step 3: Write `plot_correlations.py` with just the functions**

```python
"""Builds correlation_heatmap.png and correlations_top_pairs.csv from
dataset.csv."""

import matplotlib

matplotlib.use("Agg")  # headless: no display in CI, and no window needed locally

import matplotlib.pyplot as plt
import pandas as pd

from chart_style import INK, INK_SECONDARY, TICK_SIZE, TITLE_SIZE

INPUT_FILE = "dataset.csv"
HEATMAP_FILE = "correlation_heatmap.png"
TOP_PAIRS_FILE = "correlations_top_pairs.csv"

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
    """Largest-magnitude correlation pairs, self-pairs and symmetric duplicates removed."""
    columns = list(corr.columns)
    rows = [
        {"column_a": col_a, "column_b": col_b, "correlation": corr.loc[col_a, col_b]}
        for i, col_a in enumerate(columns)
        for col_b in columns[i + 1 :]
    ]
    result = pd.DataFrame(rows)
    result["abs_correlation"] = result["correlation"].abs()
    result = result.sort_values("abs_correlation", ascending=False).drop(columns="abs_correlation")
    return result.head(n).reset_index(drop=True)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `source .venv/Scripts/activate && python -m pytest tests/test_correlations.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add plot_correlations.py tests/test_correlations.py
git commit -m "$(cat <<'EOF'
Add correlation matrix pure functions

compute_correlation_matrix() selects the continuous numeric columns
(popularity, duration, 9 audio features) and top_pairs() ranks the
strongest relationships by absolute value, with self-pairs and
symmetric duplicates removed.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: `plot_correlations.py` — wire up the full script

**Files:**
- Modify: `plot_correlations.py`

- [ ] **Step 1: Add heatmap plotting and `main()` to `plot_correlations.py`**

Append to the end of `plot_correlations.py`:

```python


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
```

- [ ] **Step 2: Run it and inspect the output**

Run: `source .venv/Scripts/activate && python plot_correlations.py`
Expected: `Gerado correlation_heatmap.png e correlations_top_pairs.csv.`

Open `correlation_heatmap.png` (Read tool or OS viewer) and confirm: 11x11 grid, all labels readable, diagonal reads 1.00, color scale matches sign (blue/red per `RdBu_r`).

Run: `cat correlations_top_pairs.csv`
Expected: 10 rows, sorted by descending absolute correlation (check the first row is the strongest relationship, e.g. `energy`/`loudness` or similar).

- [ ] **Step 3: Run the existing test suite to confirm nothing broke**

Run: `source .venv/Scripts/activate && python -m pytest tests/ -v`
Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add plot_correlations.py correlation_heatmap.png correlations_top_pairs.csv
git commit -m "$(cat <<'EOF'
Generate correlation heatmap and top-pairs report

plot_correlations.py now writes correlation_heatmap.png (11x11,
popularity + duration + 9 audio features) and
correlations_top_pairs.csv (10 strongest relationships) that the
site's upcoming correlacoes.html page will read.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Generalize `analise.html` and migrate the existing static pages

**Files:**
- Modify: `site/templates/analise.html`
- Modify: `site/build_site.py`

`modo.html` and `popularidade.html` currently pass a single `image`/`image_alt`/`caption`.
This task changes the template to accept `tiles` (optional), `figures` (a list), and
`table` (optional), and migrates those two pages' `build_site.py` entries to the new
shape — their rendered HTML output must not change.

- [ ] **Step 1: Replace `site/templates/analise.html`**

```html
{% extends "base.html" %}
{% block content %}
<div class="page">
  <header>
    <p class="eyebrow">{{ eyebrow }}</p>
    <h1>{{ heading }}</h1>
    <p>{{ description }}</p>
  </header>

  {% if tiles %}
  <div class="tiles">
    {% for tile in tiles %}
    <div class="tile">
      <div class="tile-label">{{ tile.label }}</div>
      <div class="tile-value">{{ tile.value }}</div>
      {% if tile.sub %}<div class="tile-sub">{{ tile.sub }}</div>{% endif %}
    </div>
    {% endfor %}
  </div>
  {% endif %}

  {% for figure in figures %}
  <section>
    <figure class="analysis-figure">
      <img src="{{ figure.image }}" alt="{{ figure.alt }}" loading="lazy">
      <figcaption>{{ figure.caption }}</figcaption>
    </figure>
  </section>
  {% endfor %}

  {% if table %}
  <section>
    <h2>{{ table.title }}</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>{% for header in table.headers %}<th>{{ header }}</th>{% endfor %}</tr>
        </thead>
        <tbody>
          {% for row in table.rows %}
          <tr>{% for cell in row %}<td>{{ cell }}</td>{% endfor %}</tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </section>
  {% endif %}
</div>
{% endblock %}
```

- [ ] **Step 2: Update `STATIC_ANALYSES` and its rendering loop in `site/build_site.py`**

Replace the `STATIC_ANALYSES` list (find it below the `ANALYSES` list) with:

```python
STATIC_ANALYSES = [
    {
        "href": "modo.html",
        "eyebrow": "Dataset Spotify · agrupado por track_genre e mode",
        "heading": "Escala (mode) por genero",
        "description": (
            "Proporcao de faixas em escala maior (mode 1) e menor (mode 0) para "
            "cada genero, calculada por groupby(\"track_genre\")[\"mode\"].mean() "
            "a partir de dataset.csv."
        ),
        "figures": [
            {
                "path": ROOT / "genre_mode.png",
                "alt": "Grafico de barras empilhadas: proporcao de escala maior e menor por genero",
            }
        ],
    },
    {
        "href": "popularidade.html",
        "eyebrow": "Dataset Spotify · agrupado por artists",
        "heading": "Popularidade media x ocorrencias do artista",
        "description": (
            "Artistas agrupados por quantidade de faixas na base (1, 2, 3, 4-5, "
            "..., 21+) e a popularidade media das faixas em cada faixa de "
            "ocorrencia."
        ),
        "figures": [
            {
                "path": ROOT / "popularity_occurrences.png",
                "alt": "Grafico de barras: popularidade media por faixa de quantidade de ocorrencias do artista",
            }
        ],
    },
]
```

Then find the `for analysis in STATIC_ANALYSES:` loop inside `build()` and replace it with:

```python
    for analysis in STATIC_ANALYSES:
        html = env.get_template("analise.html").render(
            title=analysis["heading"],
            eyebrow=analysis["eyebrow"],
            heading=analysis["heading"],
            description=analysis["description"],
            figures=[
                {"image": fig["path"].name, "alt": fig["alt"], "caption": fig["path"].name}
                for fig in analysis["figures"]
            ],
        )
        (DIST_DIR / analysis["href"]).write_text(html, encoding="utf-8")
```

Finally, find the `all_pngs = GENRE_PNGS + [...]` line and replace it with:

```python
    all_pngs = GENRE_PNGS + [
        fig["path"] for analysis in STATIC_ANALYSES for fig in analysis["figures"]
    ]
```

- [ ] **Step 3: Run the full pipeline and diff the two migrated pages**

Run:
```bash
source .venv/Scripts/activate
python site/build_site.py
grep -c "{{" site/dist/modo.html site/dist/popularidade.html
```
Expected: `0` for both files.

Read `site/dist/modo.html` and `site/dist/popularidade.html` (Read tool) and confirm each
still has exactly one `<figure class="analysis-figure">` with the correct `img src` and
`figcaption`, and no `<div class="tiles">` or table markup (since neither entry sets
`tiles`/`table`).

- [ ] **Step 4: Run the test suite**

Run: `source .venv/Scripts/activate && python -m pytest tests/ -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add site/templates/analise.html site/build_site.py
git commit -m "$(cat <<'EOF'
Generalize analise.html to support tiles, multiple figures, a table

modo.html and popularidade.html migrate to the new figures-list
shape with no change in rendered output. This unblocks the upcoming
visao-geral.html and correlacoes.html pages, which need stat tiles
and a data table alongside their images.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Wire `visao-geral.html` and `correlacoes.html` into `build_site.py`

**Files:**
- Modify: `site/build_site.py`

- [ ] **Step 1: Add new constants and loader helpers**

Find the `GENRE_CSV`/`GENRE_PNGS` constants near the top of `site/build_site.py` and add
after them:

```python
PROFILE_JSON = ROOT / "dataset_profile.json"
MULTI_GENRE_CSV = ROOT / "dataset_multi_genre_tracks.csv"
ARTIST_DIST_PNG = ROOT / "artist_track_distribution.png"
ALBUM_DIST_PNG = ROOT / "album_track_distribution.png"

CORRELATIONS_CSV = ROOT / "correlations_top_pairs.csv"
CORRELATION_HEATMAP_PNG = ROOT / "correlation_heatmap.png"
```

Then find the `ANALYSES` list and add two entries after `"popularidade"`:

```python
    {
        "id": "visao-geral",
        "title": "Visao Geral do Dataset",
        "description": "Estatisticas gerais, duplicatas e distribuicao de faixas por artista/album.",
        "href": "visao-geral.html",
    },
    {
        "id": "correlacoes",
        "title": "Correlacoes",
        "description": "Correlacao entre popularidade, duracao e features de audio.",
        "href": "correlacoes.html",
    },
```

Then, after the `rows_to_embeddable_json` function, add two loader functions:

```python
def load_profile_tiles(profile_path: Path) -> list[dict]:
    """Turn dataset_profile.json into the tile list visao-geral.html renders."""
    with open(profile_path, encoding="utf-8") as f:
        profile = json.load(f)
    total_nulls = sum(profile["null_counts"].values())
    return [
        {"label": "Faixas na base", "value": f"{profile['total_tracks']:,}".replace(",", ".")},
        {
            "label": "Faixas unicas",
            "value": f"{profile['unique_track_ids']:,}".replace(",", "."),
            "sub": f"{profile['duplicate_rows']} linhas duplicadas (mesma faixa em outro genero)",
        },
        {"label": "Artistas", "value": f"{profile['unique_artists']:,}".replace(",", ".")},
        {"label": "Albuns", "value": f"{profile['unique_albums']:,}".replace(",", ".")},
        {"label": "Generos", "value": str(profile["unique_genres"])},
        {"label": "Valores nulos", "value": str(total_nulls)},
    ]


def load_table_rows(csv_path: Path, columns: list[str], round_cols: dict[str, int] | None = None) -> list[list]:
    """Read a CSV into the row-of-lists shape analise.html's table block needs."""
    df = pd.read_csv(csv_path)
    for col, digits in (round_cols or {}).items():
        df[col] = df[col].round(digits)
    return df[columns].values.tolist()
```

- [ ] **Step 2: Render the two new pages in `build()`**

Find the end of the `for analysis in STATIC_ANALYSES:` loop in `build()` (added in Task 5)
and insert this immediately after it, still inside `build()`:

```python

    visao_geral_html = env.get_template("analise.html").render(
        title="Visao Geral do Dataset",
        eyebrow="Dataset Spotify · visao geral",
        heading="Visao Geral do Dataset",
        description=(
            "31819 linhas no dataset bruto, mas nem toda linha e uma faixa "
            "distinta: a mesma musica pode aparecer sob mais de um genero. "
            "Numeros calculados diretamente de dataset.csv."
        ),
        tiles=load_profile_tiles(PROFILE_JSON),
        figures=[
            {
                "image": ARTIST_DIST_PNG.name,
                "alt": "Grafico de barras: quantidade de artistas por faixa de numero de musicas na base",
                "caption": ARTIST_DIST_PNG.name,
            },
            {
                "image": ALBUM_DIST_PNG.name,
                "alt": "Grafico de barras: quantidade de albuns por faixa de numero de musicas na base",
                "caption": ALBUM_DIST_PNG.name,
            },
        ],
        table={
            "title": "Faixas presentes em mais generos",
            "headers": ["Faixa", "Artista", "Generos distintos"],
            "rows": load_table_rows(MULTI_GENRE_CSV, ["track_name", "artists", "genre_count"]),
        },
    )
    (DIST_DIR / "visao-geral.html").write_text(visao_geral_html, encoding="utf-8")

    correlacoes_html = env.get_template("analise.html").render(
        title="Correlacoes",
        eyebrow="Dataset Spotify · correlacao entre variaveis numericas",
        heading="Correlacoes entre popularidade, duracao e audio",
        description=(
            "Correlacao de Pearson entre popularidade, duracao e as 9 features "
            "de audio continuas do dataset (key, mode e time_signature ficam "
            "de fora por nao serem continuas)."
        ),
        figures=[
            {
                "image": CORRELATION_HEATMAP_PNG.name,
                "alt": "Heatmap de correlacao entre popularidade, duracao e features de audio",
                "caption": CORRELATION_HEATMAP_PNG.name,
            },
        ],
        table={
            "title": "Pares mais correlacionados",
            "headers": ["Variavel A", "Variavel B", "Correlacao"],
            "rows": load_table_rows(
                CORRELATIONS_CSV, ["column_a", "column_b", "correlation"], round_cols={"correlation": 3}
            ),
        },
    )
    (DIST_DIR / "correlacoes.html").write_text(correlacoes_html, encoding="utf-8")
```

- [ ] **Step 3: Copy the new PNGs into `site/dist/`**

Find the `all_pngs = GENRE_PNGS + [...]` line (from Task 5) and replace it with:

```python
    all_pngs = (
        GENRE_PNGS
        + [fig["path"] for analysis in STATIC_ANALYSES for fig in analysis["figures"]]
        + [ARTIST_DIST_PNG, ALBUM_DIST_PNG, CORRELATION_HEATMAP_PNG]
    )
```

- [ ] **Step 4: Run the full pipeline end to end**

Run:
```bash
source .venv/Scripts/activate
python group_occurrences.py
python plot_genre_charts.py
python plot_genre_mode.py
python plot_popularity_occurrences.py
python profile_dataset.py
python plot_correlations.py
python site/build_site.py
ls site/dist
grep -c "{{" site/dist/*.html
```
Expected: `site/dist` contains `index.html`, `genero.html`, `modo.html`, `popularidade.html`,
`visao-geral.html`, `correlacoes.html`, `static/`, and all 7 PNGs; `grep -c "{{"` prints `0`
for every HTML file.

- [ ] **Step 5: Visual check**

```bash
start site/dist/index.html
```
(On Windows this opens the default browser via the `start` command run through git-bash;
use `Start-Process site/dist/index.html` if running this step in PowerShell instead.)

Confirm:
- Hub page shows 5 cards, including "Visao Geral do Dataset" and "Correlacoes".
- `visao-geral.html`: 6 stat tiles, two distribution charts, and a 15-row table sorted by
  genre count descending.
- `correlacoes.html`: the heatmap image and a 10-row table of the strongest correlations.
- Dark mode (toggle OS theme) still renders both new pages correctly — they reuse existing
  `.tiles`/`.analysis-figure`/`table` CSS, so no new styling is expected to be needed.

- [ ] **Step 6: Run the test suite**

Run: `source .venv/Scripts/activate && python -m pytest tests/ -v`
Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add site/build_site.py
git commit -m "$(cat <<'EOF'
Render visao-geral.html and correlacoes.html

Wires dataset_profile.json, the two distribution PNGs, the
multi-genre-tracks CSV, the correlation heatmap, and the top-pairs
CSV into two new site pages via the generalized analise.html
template, and adds their hub cards.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: Add the new scripts to the GitHub Actions workflow

**Files:**
- Modify: `.github/workflows/pages.yml`

- [ ] **Step 1: Add the two new pipeline steps**

In `.github/workflows/pages.yml`, find:

```yaml
      - run: python group_occurrences.py
      - run: python plot_genre_charts.py
      - run: python plot_genre_mode.py
      - run: python plot_popularity_occurrences.py
      - run: python site/build_site.py
```

Replace with:

```yaml
      - run: python group_occurrences.py
      - run: python plot_genre_charts.py
      - run: python plot_genre_mode.py
      - run: python plot_popularity_occurrences.py
      - run: python profile_dataset.py
      - run: python plot_correlations.py
      - run: python site/build_site.py
```

- [ ] **Step 2: Validate the YAML parses**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/pages.yml')); print('valid')"`
Expected: `valid`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/pages.yml
git commit -m "$(cat <<'EOF'
Run profile_dataset.py and plot_correlations.py in the Pages workflow

Both scripts' outputs are now required by site/build_site.py's
visao-geral.html and correlacoes.html pages.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 8: Update `README.md`

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add the new outputs to "Estrutura do repositório"**

Find this block in `README.md`:

```
group_occurrences.py           # agrupa dataset.csv por coluna e por track_genre
occurrences_by_column.csv      # contagem de valores por coluna (formato longo)
occurrences_by_genre.csv       # contagem de faixas + médias por gênero
plot_genre_charts.py           # gera genre_popularity.png e genre_energy_dance.png
plot_genre_mode.py             # gera genre_mode.png (proporção de escala maior/menor)
plot_popularity_occurrences.py # gera popularity_occurrences.png (popularidade x nº de faixas do artista)
docs/                          # specs e planos de implementação (superpowers)
```

Replace with:

```
group_occurrences.py           # agrupa dataset.csv por coluna e por track_genre
occurrences_by_column.csv      # contagem de valores por coluna (formato longo)
occurrences_by_genre.csv       # contagem de faixas + médias por gênero
plot_genre_charts.py           # gera genre_popularity.png e genre_energy_dance.png
plot_genre_mode.py             # gera genre_mode.png (proporção de escala maior/menor)
plot_popularity_occurrences.py # gera popularity_occurrences.png (popularidade x nº de faixas do artista)
profile_dataset.py             # gera dataset_profile.json e distribuições de faixas por artista/álbum
plot_correlations.py           # gera correlation_heatmap.png e correlations_top_pairs.csv
site/                          # gera o site GitHub Pages (site/build_site.py) a partir dos CSVs/PNGs acima
docs/                          # specs e planos de implementação (superpowers)
```

- [ ] **Step 2: Add the two new analyses to "Análises disponíveis"**

Find this block:

```
- **`popularity_occurrences.png`** — relação entre popularidade média e
  quantidade de faixas do artista na base (proxy de volume de catálogo).
```

Replace with:

```
- **`popularity_occurrences.png`** — relação entre popularidade média e
  quantidade de faixas do artista na base (proxy de volume de catálogo).
- **`dataset_profile.json` / `artist_track_distribution.png` /
  `album_track_distribution.png`** — visão geral do dataset: contagem de
  faixas, artistas, álbuns e gêneros, faixas duplicadas entre gêneros, e
  distribuição de faixas por artista/álbum.
- **`correlation_heatmap.png`** — correlação de Pearson entre popularidade,
  duração e as 9 features de áudio contínuas.
```

- [ ] **Step 3: Add the two scripts to "Como reproduzir"**

Find this block:

```bash
pip install pandas matplotlib
python group_occurrences.py          # gera os CSVs agregados
python plot_genre_charts.py          # gera genre_popularity.png e genre_energy_dance.png
python plot_genre_mode.py            # gera genre_mode.png
python plot_popularity_occurrences.py # gera popularity_occurrences.png
```

Replace with:

```bash
pip install pandas matplotlib
python group_occurrences.py          # gera os CSVs agregados
python plot_genre_charts.py          # gera genre_popularity.png e genre_energy_dance.png
python plot_genre_mode.py            # gera genre_mode.png
python plot_popularity_occurrences.py # gera popularity_occurrences.png
python profile_dataset.py            # gera dataset_profile.json e distribuicoes por artista/album
python plot_correlations.py          # gera correlation_heatmap.png e correlations_top_pairs.csv
```

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "$(cat <<'EOF'
Document the dataset overview and correlation analyses in the README

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 9: Push and verify the deploy (requires explicit confirmation)

**This task is not autonomous.** It pushes to `origin/main`, which triggers a live
GitHub Pages deploy. Confirm with the user before running any command below.

- [ ] **Step 1: Confirm with the user, then push**

The site work happens on the `worktree-github-pages-site` branch and is pushed straight
to `origin`'s `main` ref (this repo's established pattern for this branch — see prior
commits):

```bash
git push origin worktree-github-pages-site:main
```

- [ ] **Step 2: Watch the workflow run**

```bash
gh run list --limit 1
gh run watch <run-id-from-above> --exit-status
```

Expected: both `build` and `deploy` jobs finish green. If `deploy` times out waiting on
`updating_pages` (seen once before during this project — a transient GitHub-side stall,
not caused by this repo's workflow), re-run it with `gh run rerun <run-id> ` and watch
again.

- [ ] **Step 3: Open the published URL and repeat the Step 5 visual checks from Task 6 against it**

`https://lucas-av.github.io/Grupo-8-ResIA/` — confirm the 5 hub cards, both new pages'
tiles/figures/tables, and dark-mode rendering match what was checked locally.
