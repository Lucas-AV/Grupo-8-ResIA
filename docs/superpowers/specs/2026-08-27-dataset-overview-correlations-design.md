# Dataset overview and correlation analyses for the site

## Context

The GitHub Pages site (`docs/superpowers/specs/2026-08-27-github-pages-site-design.md`,
implemented) currently publishes three analyses, all scoped to `track_genre`:
`genero.html` (interactive), `modo.html` and `popularidade.html` (static PNG
pages, most recently added). There is no page that describes the dataset as a
whole (row counts, uniqueness, data-quality quirks) or that looks at how
numeric variables relate to each other across the full table.

Goal: add two more analyses — a dataset overview and a correlation study —
using the same root-script-produces-CSV/PNG, `build_site.py`-renders-templates
pipeline as the existing analyses.

## Non-goals

- No new Python dependency (correlation heatmap uses matplotlib directly, no
  seaborn).
- No interactive/JS charts for these two pages — static images + Jinja-rendered
  tiles/tables, consistent with the `modo.html`/`popularidade.html` pattern.
- No changes to the existing `genero.html`, `modo.html`, `popularidade.html`
  content beyond what `analise.html`'s generalization requires structurally.

## Data findings (from an ad-hoc profiling pass on `dataset.csv`)

31819 rows, 28888 unique `track_id` (2931 rows are the same track re-listed
under a different `track_genre` — a known quirk of this Kaggle dataset, not a
data error), 10872 unique `artists`, 15481 unique `album_name`, 32
`track_genre` values, zero nulls in any column.

## Architecture

```
profile_dataset.py              # dataset-wide stats + artist/album distributions
plot_correlations.py            # correlation matrix across numeric audio features
dataset_profile.json            # summary stats consumed by build_site.py
dataset_multi_genre_tracks.csv  # top tracks appearing under multiple genres
artist_track_distribution.png
album_track_distribution.png
correlations_top_pairs.csv      # top 10 |correlation| pairs
correlation_heatmap.png
site/
  templates/
    analise.html                # generalized: optional tiles, multiple figures, one table
```

## Data flow

1. `profile_dataset.py` reads `dataset.csv` and computes:
   - `compute_profile(df) -> dict`: total tracks, unique `track_id`, duplicate
     row count, unique artists, unique albums, unique genres, null counts per
     column. Written to `dataset_profile.json`.
   - Artist and album track-count distributions, bucketed with the same edges
     as `plot_popularity_occurrences.py` (`1, 2, 3, 4-5, 6-10, 11-20, 21+`),
     counting artists/albums per bucket (not popularity this time). Rendered
     as `artist_track_distribution.png` and `album_track_distribution.png`
     via `chart_style.py`.
   - Top 15 (track_name, artists) pairs by distinct `track_genre` count, for
     `dataset_multi_genre_tracks.csv`.
2. `plot_correlations.py` reads `dataset.csv`, computes a Pearson correlation
   matrix over `popularity`, `duration_ms`, `danceability`, `energy`,
   `loudness`, `speechiness`, `acousticness`, `instrumentalness`, `liveness`,
   `valence`, `tempo` (continuous audio features; `key`/`mode`/
   `time_signature`/`explicit` excluded as non-continuous). One heatmap
   (`correlation_heatmap.png`) covers audio-feature-vs-feature,
   popularity-vs-feature, and duration-vs-feature correlations at once. The 10
   largest-magnitude pairs (self-pairs and symmetric duplicates removed) go to
   `correlations_top_pairs.csv`.
3. `site/build_site.py` reads `dataset_profile.json`,
   `dataset_multi_genre_tracks.csv`, and `correlations_top_pairs.csv`, and
   renders two new pages through the generalized `analise.html` template.

## Template generalization

`analise.html` currently renders one `image`. It becomes:

- `tiles` (optional list of `{label, value, sub?}`) — same tile markup as
  `genero.html`'s stat tiles.
- `figures` (list of `{image, alt, caption}`, replacing the single `image` var)
  — one `<figure>` per entry.
- `table` (optional `{title, headers, rows}`) — plain Jinja-rendered table, no
  sorting JS (rows are small: 15 and 10 respectively).

`modo.html` and `popularidade.html`'s `build_site.py` entries move from a
single `image`/`image_alt`/`caption` to a one-item `figures` list; their
rendered output is unchanged.

## Site content

- **`visao-geral.html`** — tiles (total faixas, faixas duplicadas entre
  generos, artistas, álbuns, generos); the two distribution PNGs; a table of
  the 15 tracks appearing under the most genres.
- **`correlacoes.html`** — the heatmap; a table of the 10 strongest
  correlation pairs (column A, column B, correlation value).
- Two new hub cards on `index.html`, same pattern as the existing three.
- `.github/workflows/pages.yml` gains `python profile_dataset.py` and
  `python plot_correlations.py` steps before `python site/build_site.py`.

## Testing / verification

Follow the existing TDD pattern (`tests/test_build_site.py`): write a failing
test first for each pure, non-plotting function, then implement.

- `tests/test_profile_dataset.py`: `compute_profile()` on a small in-memory
  frame; bucket-counting helper on a small series.
- `tests/test_correlations.py`: `compute_correlation_matrix()` column
  selection; `top_pairs()` ordering, dedup, and self-pair exclusion on a small
  fixed correlation matrix.
- No automated test for PNG rendering or template output — verified by running
  the full pipeline, checking `grep -c "{{"` is 0 on the new HTML files, and
  visual inspection of the two new pages plus the two migrated static pages
  (to confirm the `figures`-list generalization didn't change their output).

## Risks / open questions

- `dataset_profile.json` is the first non-CSV pipeline output in this repo;
  chosen because it's a single summary record, not tabular data — CSV would
  need an awkward single-row shape. `build_site.py` reads it with the stdlib
  `json` module (already imported).
- The duplicate-`track_id` rows are expected (multi-genre tagging), not a bug;
  the overview page states this explicitly so it doesn't read as a data
  problem.
