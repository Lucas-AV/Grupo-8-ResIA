# GitHub Pages site for repo analyses

## Context

The repo analyzes a Spotify tracks dataset (`dataset.csv`). Today it has:

- `group_occurrences.py` — generates `occurrences_by_column.csv` and `occurrences_by_genre.csv`.
- `plot_genre_charts.py` — generates `genre_popularity.png` (ranked bar) and
  `genre_energy_dance.png` (energy vs. danceability scatter).
- A hand-built interactive HTML dashboard was published once as a Claude Artifact
  ("Perfil Sonoro") but does not live in the repo or auto-update.

Goal: publish a GitHub Pages site, built and deployed automatically, that hosts
the interactive dashboard (and, over time, additional analyses) plus the static
chart exports. Also improve the readability of the matplotlib charts, especially
the scatter plot's overlapping genre labels.

## Non-goals

- No reorganization of the existing analysis scripts' location (they stay at repo root).
- No new analyses beyond genre (future analyses are out of scope; this design only
  makes adding them cheap).
- No authentication/private hosting — GitHub Pages is public, matching the repo's
  visibility.

## Architecture

```
chart_style.py                 # shared matplotlib style/palette helpers
requirements.txt               # pandas, matplotlib, adjustText, Jinja2
site/
  build_site.py                # reads CSVs, renders templates -> site/dist/
  templates/
    base.html                  # nav, footer, shared CSS tokens (Jinja2 block layout)
    index.html                 # hub: one card per analysis
    genero.html                # genre dashboard (extends base.html)
  static/
    style.css                  # shared design tokens/components, light+dark
.github/workflows/pages.yml    # CI: run pipeline, deploy to Pages
```

`site/dist/` is the build output (gitignored, not committed) — CI regenerates it
every run and uploads it as the Pages artifact.

## Data flow

1. `group_occurrences.py` reads `dataset.csv`, writes `occurrences_by_column.csv`
   and `occurrences_by_genre.csv` (unchanged behavior).
2. `plot_genre_charts.py` reads `occurrences_by_genre.csv`, writes
   `genre_popularity.png` and `genre_energy_dance.png`, now using shared
   `chart_style.py` helpers and `adjustText` for the scatter labels.
3. `site/build_site.py` reads `occurrences_by_genre.csv`, converts rows to JSON,
   renders `templates/index.html` and `templates/genero.html` via Jinja2 into
   `site/dist/index.html` and `site/dist/genero.html`, and copies
   `genre_popularity.png`, `genre_energy_dance.png`, and `site/static/` into
   `site/dist/`.

Each analysis page is self-contained: the interactive charts (bars, scatter,
sortable table) are inline SVG/JS reading from the JSON the build script embeds,
same technique as the earlier hand-built dashboard, just automated.

## Site content

- **`index.html`** — hub page. Header + a card grid; today one card ("Perfil dos
  Gêneros" → `genero.html`). Adding a future analysis means: write its Python
  pipeline (own CSV/PNG outputs), add a template extending `base.html`, add one
  entry to the `ANALYSES` list in `build_site.py`. No changes to `base.html` or
  `index.html`'s structure needed.
- **`genero.html`** — the interactive dashboard: stat tiles (genres analyzed,
  total tracks, most popular, most energetic), ranked popularity bar chart,
  energy-vs-danceability scatter, sortable full data table — content ported from
  the previously published "Perfil Sonoro" artifact. Below the interactive
  section, a "Exportar" block embeds the two static PNGs for anyone who wants a
  non-interactive/printable view.
- **`base.html` / `style.css`** — shared nav ("Análises" link back to hub),
  footer, and the design tokens (color, type) so every future analysis page
  inherits the same look without duplicating CSS.

## Chart legibility fixes (`plot_genre_charts.py`, `chart_style.py`)

- New `chart_style.py` centralizes the accent color, ink colors, grid color, and
  an `apply_style(ax)` helper (spines, tick colors, grid) — currently duplicated
  inline in `plot_genre_charts.py`. Future analysis scripts import this instead
  of redefining constants.
- Scatter (`genre_energy_dance.png`): use `adjustText.adjust_text()` to
  auto-resolve the overlapping labels in the dense central cluster, with thin
  leader lines connecting label to point. Slightly larger figure size.
- Both charts: bump base font sizes (title, axis labels, tick labels) and DPI
  for sharper text at normal viewing/embed size.

## CI / deployment (`.github/workflows/pages.yml`)

Trigger: push to `main`. Steps: checkout → setup Python → `pip install -r
requirements.txt` → run `group_occurrences.py` → run `plot_genre_charts.py` →
run `site/build_site.py` → `actions/upload-pages-artifact` on `site/dist/` →
`actions/deploy-pages`. Permissions: `pages: write`, `id-token: write`.
`dataset.csv` stays committed in the repo; the workflow reads it directly (no
Git LFS, no external download — accepted repo-size tradeoff per user decision).

GitHub Pages must be switched to "GitHub Actions" as its source in the repo
settings (one-time manual step, not scriptable from here — will be called out
at the end of implementation).

## Testing / verification

- Run `group_occurrences.py` → `plot_genre_charts.py` → `site/build_site.py`
  locally; open `site/dist/index.html` and `site/dist/genero.html` in a browser
  and confirm: nav works, stat tiles/bars/scatter/table render and match the CSV
  data, dark mode looks correct, PNGs embed and are legible (no overlapping
  scatter labels).
- No automated test suite exists in this repo; verification is manual browser
  inspection plus confirming each script exits 0.
- CI success is verified by watching the workflow run green and the Pages URL
  serving the expected content after the one-time Pages-source switch.

## Risks / open questions

- The repo's local Python environment has pinned-down numpy/pandas/matplotlib
  versions to avoid an ABI conflict (see prior session). CI runs in a clean
  `ubuntu-latest` environment, so `requirements.txt` will pin modern compatible
  versions independently — this is not expected to reproduce the local conflict,
  but is worth confirming once the workflow runs.
