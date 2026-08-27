# GitHub Pages Analyses Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a GitHub Pages site (deployed via GitHub Actions) that hosts an interactive genre-analysis dashboard plus static chart exports, and fix the readability problems in the existing matplotlib charts.

**Architecture:** Two existing root-level scripts (`group_occurrences.py`, `plot_genre_charts.py`) keep producing CSVs/PNGs from `dataset.csv`. A new `site/build_site.py` reads those CSVs and renders Jinja2 templates into `site/dist/`, which a GitHub Actions workflow uploads as the Pages artifact on every push to `main`. A new `chart_style.py` centralizes matplotlib styling so `plot_genre_charts.py` and future analysis scripts share one look, and `adjustText` fixes the scatter chart's overlapping genre labels.

**Tech Stack:** Python 3, pandas, matplotlib, adjustText, Jinja2, pytest, GitHub Actions (`actions/upload-pages-artifact`, `actions/deploy-pages`).

Reference spec: `docs/superpowers/specs/2026-08-27-github-pages-site-design.md`

---

### Task 1: Project tooling — requirements.txt, venv, .gitignore

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `.venv/` (local virtual environment, not committed)

The repo's global Python install currently has numpy/pandas/matplotlib pinned to
older mutually-compatible versions to dodge an ABI conflict from a previous
session. Rather than fight that further, this task creates an isolated `.venv`
for this repo so `requirements.txt` can specify modern versions without
touching global site-packages.

- [ ] **Step 1: Write `requirements.txt`**

```
pandas>=2.2,<3
matplotlib>=3.8,<4
adjustText>=1.1,<2
Jinja2>=3.1,<4
pytest>=7.4,<8
```

- [ ] **Step 2: Create the virtual environment**

Run: `python -m venv .venv`
Expected: creates `.venv/` with no output.

- [ ] **Step 3: Install dependencies into the venv and verify imports**

Run:
```bash
source .venv/Scripts/activate
pip install -r requirements.txt
python -c "import pandas, matplotlib, adjustText, jinja2, pytest; print('ok')"
```
Expected: last line prints `ok` with no import errors.

- [ ] **Step 4: Write `.gitignore`**

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
site/dist/
```

- [ ] **Step 5: Commit tooling files plus the pre-existing untracked pipeline outputs**

These files were generated in a prior session and never committed — commit
them now since the site build depends on them.

```bash
git add requirements.txt .gitignore group_occurrences.py occurrences_by_column.csv occurrences_by_genre.csv
git commit -m "$(cat <<'EOF'
Add project tooling and commit genre grouping pipeline

requirements.txt + .venv keep this repo's Python deps isolated from
the global install's pinned versions. group_occurrences.py and its
CSV outputs were generated in a prior session and were never
committed.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Shared matplotlib style module

**Files:**
- Create: `chart_style.py`
- Create: `conftest.py`
- Test: `tests/test_chart_style.py`

`conftest.py` at the repo root has pytest add the repo root to `sys.path`, so
test files can `import chart_style` (and, in later tasks, `import
build_site`-style helpers) without path hacks in every test file.

- [ ] **Step 1: Write the failing test**

Create `conftest.py` (empty — its presence is what makes pytest add the repo
root to `sys.path`):

```python
```

Create `tests/test_chart_style.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `source .venv/Scripts/activate && python -m pytest tests/test_chart_style.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'chart_style'`

- [ ] **Step 3: Write `chart_style.py`**

```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `source .venv/Scripts/activate && python -m pytest tests/test_chart_style.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add conftest.py chart_style.py tests/test_chart_style.py
git commit -m "$(cat <<'EOF'
Add shared chart_style module for matplotlib scripts

Centralizes the accent/ink/grid colors and axis styling so every
chart-producing script shares one look instead of redefining
constants inline.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Fix scatter label overlap and bump chart legibility

**Files:**
- Modify: `plot_genre_charts.py` (full rewrite of its body)

`adjustText.adjust_text` auto-repels overlapping labels and draws a thin
leader line back to each point. This task also raises figure size, DPI, and
font sizes using the new `chart_style` constants. There's no automated test
here — matplotlib output correctness is verified visually by opening the
generated PNGs.

- [ ] **Step 1: Rewrite `plot_genre_charts.py`**

```python
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

INPUT_FILE = "occurrences_by_genre.csv"
BAR_OUTPUT_FILE = "genre_popularity.png"
SCATTER_OUTPUT_FILE = "genre_energy_dance.png"


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
    fig, ax = plt.subplots(figsize=(10, 10), dpi=150)
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
```

- [ ] **Step 2: Run it and inspect the output**

Run: `source .venv/Scripts/activate && python plot_genre_charts.py`
Expected: `Gerado genre_popularity.png e genre_energy_dance.png.`

Open both PNGs (e.g. with the Read tool, or your OS image viewer) and confirm:
- `genre_energy_dance.png`: every genre label is readable, none overlap another
  label or a point it doesn't belong to; thin leader lines connect labels that
  moved away from their point.
- `genre_popularity.png`: title/axis/tick text is crisp at normal viewing size.

- [ ] **Step 3: Commit**

```bash
git add plot_genre_charts.py genre_popularity.png genre_energy_dance.png
git commit -m "$(cat <<'EOF'
Fix overlapping scatter labels and bump chart legibility

Use adjustText to auto-repel the genre_energy_dance.png labels
instead of overlapping in the dense central cluster. Also share
chart_style constants and raise figure size/DPI/font sizes on both
charts.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Genre data loader for the site build

**Files:**
- Create: `site/build_site.py` (loader function only in this task; rendering added in Task 6)
- Test: `tests/test_build_site.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_build_site.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "site"))

from build_site import load_genre_rows


def test_load_genre_rows_maps_and_rounds_columns(tmp_path):
    csv_path = tmp_path / "occurrences_by_genre.csv"
    csv_path.write_text(
        "track_genre,contagem,popularity,duration_ms,danceability,energy,key,"
        "loudness,mode,speechiness,acousticness,instrumentalness,liveness,"
        "valence,tempo,time_signature\n"
        "acoustic,1000,42.4834,214896.957,0.549593,0.435368,5.045,-9.447843,"
        "0.816,0.043247,0.566816,0.038336,0.153244,0.424023,119.010624,3.885\n",
        encoding="utf-8",
    )

    rows = load_genre_rows(csv_path)

    assert rows == [
        {
            "g": "acoustic",
            "n": 1000,
            "pop": 42.5,
            "dance": 0.55,
            "energy": 0.435,
            "tempo": 119.0,
            "valence": 0.424,
            "acoustic": 0.567,
        }
    ]


def test_load_genre_rows_preserves_csv_row_order(tmp_path):
    csv_path = tmp_path / "occurrences_by_genre.csv"
    csv_path.write_text(
        "track_genre,contagem,popularity,duration_ms,danceability,energy,key,"
        "loudness,mode,speechiness,acousticness,instrumentalness,liveness,"
        "valence,tempo,time_signature\n"
        "b-genre,10,20,200000,0.5,0.5,5,-6,0.5,0.1,0.1,0.1,0.1,0.5,120,4\n"
        "a-genre,20,30,200000,0.5,0.5,5,-6,0.5,0.1,0.1,0.1,0.1,0.5,120,4\n",
        encoding="utf-8",
    )

    rows = load_genre_rows(csv_path)

    assert [row["g"] for row in rows] == ["b-genre", "a-genre"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `source .venv/Scripts/activate && python -m pytest tests/test_build_site.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build_site'`

- [ ] **Step 3: Write `site/build_site.py` with just the loader**

```python
"""Builds the static GitHub Pages site into site/dist/."""

from pathlib import Path

import pandas as pd


def load_genre_rows(csv_path: Path) -> list[dict]:
    """Read occurrences_by_genre.csv into the compact row shape the dashboard needs."""
    df = pd.read_csv(csv_path)
    rows = []
    for _, row in df.iterrows():
        rows.append(
            {
                "g": row["track_genre"],
                "n": int(row["contagem"]),
                "pop": round(float(row["popularity"]), 1),
                "dance": round(float(row["danceability"]), 3),
                "energy": round(float(row["energy"]), 3),
                "tempo": round(float(row["tempo"]), 1),
                "valence": round(float(row["valence"]), 3),
                "acoustic": round(float(row["acousticness"]), 3),
            }
        )
    return rows
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `source .venv/Scripts/activate && python -m pytest tests/test_build_site.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add site/build_site.py tests/test_build_site.py
git commit -m "$(cat <<'EOF'
Add genre CSV loader for the site build

load_genre_rows() maps occurrences_by_genre.csv into the compact
dict shape the dashboard's embedded JSON needs, with fields rounded
to display precision.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Site templates and shared stylesheet

**Files:**
- Create: `site/templates/base.html`
- Create: `site/templates/index.html`
- Create: `site/templates/genero.html`
- Create: `site/static/style.css`

These are HTML/CSS/Jinja2 templates — no automated tests. They're verified in
Task 6 once `build_site.py` can render them.

- [ ] **Step 1: Create `site/templates/base.html`**

```html
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }} &middot; Analises Grupo 8</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@600;700;800&family=Source+Sans+3:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="static/style.css">
</head>
<body>
<div class="site">
  <nav class="site-nav">
    <a class="site-nav-brand" href="index.html">Grupo 8 &middot; Analises</a>
    <a class="site-nav-link" href="index.html">Analises</a>
  </nav>
  <main class="site-main">
    {% block content %}{% endblock %}
  </main>
  <footer class="site-footer">
    Gerado automaticamente a partir de <code>dataset.csv</code> &middot;
    <a href="https://github.com/Lucas-AV/Grupo-8-ResIA">repositorio</a>
  </footer>
</div>
{% block scripts %}{% endblock %}
</body>
</html>
```

- [ ] **Step 2: Create `site/templates/index.html`**

```html
{% extends "base.html" %}
{% block content %}
<header class="hub-header">
  <p class="eyebrow">Dataset Spotify &middot; groupby</p>
  <h1>Analises</h1>
  <p>Exploracoes do dataset de faixas do Spotify, geradas automaticamente pelos
    scripts deste repositorio a cada atualizacao.</p>
</header>
<div class="card-grid">
  {% for analysis in analyses %}
  <a class="card" href="{{ analysis.href }}">
    <h2>{{ analysis.title }}</h2>
    <p>{{ analysis.description }}</p>
  </a>
  {% endfor %}
</div>
{% endblock %}
```

- [ ] **Step 3: Create `site/templates/genero.html`**

```html
{% extends "base.html" %}
{% block content %}
<div class="page">

  <header>
    <p class="eyebrow">Dataset Spotify &middot; agrupado por track_genre</p>
    <h1>Perfil Sonoro dos Generos</h1>
    <p>33 generos, cada um com 1.000 faixas na amostra (exceto <em>electro</em>,
      com 819). Os graficos abaixo cruzam popularidade media e caracteristicas
      de audio calculadas por <code>groupby(track_genre)</code> a partir de
      <code>dataset.csv</code>.</p>
  </header>

  <div class="tiles" id="tiles"></div>

  <section>
    <h2>Popularidade media por genero</h2>
    <p class="section-sub">Faixas ordenadas do genero mais popular ao menos popular (escala 0&ndash;100).</p>
    <div class="chart-wrap" id="barWrap">
      <svg id="barChart" width="100%"></svg>
      <div class="tooltip" id="barTooltip"></div>
    </div>
  </section>

  <section>
    <h2>Energia &times; Dancabilidade</h2>
    <p class="section-sub">Cada ponto e um genero. Canto superior direito = alta energia e alta dancabilidade.</p>
    <div class="chart-wrap" id="scatterWrap">
      <svg id="scatterChart" width="100%" viewBox="0 0 640 460"></svg>
      <div class="tooltip" id="scatterTooltip"></div>
    </div>
  </section>

  <section>
    <h2>Exportar</h2>
    <p class="section-sub">Versoes estaticas (PNG) dos mesmos dados, geradas por <code>plot_genre_charts.py</code>.</p>
    <div class="export-grid">
      <figure>
        <img src="genre_popularity.png" alt="Grafico de barras: popularidade media por genero" loading="lazy">
        <figcaption>genre_popularity.png</figcaption>
      </figure>
      <figure>
        <img src="genre_energy_dance.png" alt="Grafico de dispersao: energia por dancabilidade, um ponto por genero" loading="lazy">
        <figcaption>genre_energy_dance.png</figcaption>
      </figure>
    </div>
  </section>

  <section>
    <h2>Tabela completa</h2>
    <p class="section-sub">Clique no cabecalho para ordenar por qualquer coluna.</p>
    <div class="table-wrap">
      <table id="dataTable">
        <thead><tr id="tableHead"></tr></thead>
        <tbody id="tableBody"></tbody>
      </table>
    </div>
  </section>

</div>
{% endblock %}

{% block scripts %}
<script>
  const data = {{ rows_json | safe }};

  const fmt1 = v => v.toFixed(1);
  const fmt2 = v => v.toFixed(2);

  const totalTracks = data.reduce((s, d) => s + d.n, 0);
  const mostPopular = [...data].sort((a, b) => b.pop - a.pop)[0];
  const mostEnergetic = [...data].sort((a, b) => b.energy - a.energy)[0];

  document.getElementById("tiles").innerHTML = `
    <div class="tile"><div class="tile-label">Generos analisados</div><div class="tile-value">${data.length}</div></div>
    <div class="tile"><div class="tile-label">Faixas no dataset</div><div class="tile-value">${totalTracks.toLocaleString("pt-BR")}</div></div>
    <div class="tile"><div class="tile-label">Mais popular</div><div class="tile-value" style="font-size:20px">${mostPopular.g}</div><div class="tile-sub">popularidade ${fmt1(mostPopular.pop)}</div></div>
    <div class="tile"><div class="tile-label">Mais energetico</div><div class="tile-value" style="font-size:20px">${mostEnergetic.g}</div><div class="tile-sub">energia ${fmt2(mostEnergetic.energy)}</div></div>
  `;

  (function renderBars() {
    const sorted = [...data].sort((a, b) => b.pop - a.pop);
    const rowH = 20, gap = 4, labelW = 128, valueW = 46, topPad = 8, chartMax = 60;
    const plotW = 560;
    const width = labelW + plotW + valueW;
    const height = topPad + sorted.length * (rowH + gap) + 26;

    const svg = document.getElementById("barChart");
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

    const ticks = [0, 15, 30, 45, 60];
    let gridSvg = ticks.map(t => {
      const x = labelW + (t / chartMax) * plotW;
      return `<line class="grid-line" x1="${x}" x2="${x}" y1="${topPad}" y2="${height - 22}"/>
              <text class="axis-label" x="${x}" y="${height - 8}" text-anchor="middle">${t}</text>`;
    }).join("");

    let rows = sorted.map((d, i) => {
      const y = topPad + i * (rowH + gap);
      const barLen = (d.pop / chartMax) * plotW;
      return `
        <g class="bar-row" data-i="${i}">
          <rect class="hit" x="0" y="${y - 2}" width="${width}" height="${rowH + gap}"></rect>
          <text class="genre-label" x="${labelW - 10}" y="${y + rowH / 2 + 4}" text-anchor="end">${d.g}</text>
          <rect class="bar" x="${labelW}" y="${y}" width="${Math.max(barLen, 3)}" height="${rowH - 4}" rx="4"></rect>
          <text class="value-label" x="${labelW + barLen + 8}" y="${y + rowH / 2 + 4}">${fmt1(d.pop)}</text>
        </g>`;
    }).join("");

    svg.innerHTML = `<line class="axis-line" x1="${labelW}" x2="${labelW}" y1="${topPad}" y2="${height - 22}"/>${gridSvg}${rows}`;

    const tooltip = document.getElementById("barTooltip");
    const wrap = document.getElementById("barWrap");
    svg.querySelectorAll(".bar-row").forEach((row, i) => {
      const d = sorted[i];
      row.addEventListener("mousemove", (e) => {
        const r = wrap.getBoundingClientRect();
        tooltip.style.left = (e.clientX - r.left) + "px";
        tooltip.style.top = (e.clientY - r.top) + "px";
        tooltip.innerHTML = `<strong>${d.g}</strong>
          <div class="row"><span>popularidade</span><span>${fmt1(d.pop)}</span></div>
          <div class="row"><span>dancabilidade</span><span>${fmt2(d.dance)}</span></div>
          <div class="row"><span>energia</span><span>${fmt2(d.energy)}</span></div>
          <div class="row"><span>tempo</span><span>${fmt1(d.tempo)} bpm</span></div>
          <div class="row"><span>valencia</span><span>${fmt2(d.valence)}</span></div>`;
        tooltip.classList.add("show");
      });
      row.addEventListener("mouseleave", () => tooltip.classList.remove("show"));
    });
  })();

  (function renderScatter() {
    const svg = document.getElementById("scatterChart");
    const pad = { l: 46, r: 20, t: 16, b: 40 };
    const w = 640, h = 460;
    const plotW = w - pad.l - pad.r, plotH = h - pad.t - pad.b;
    const x = v => pad.l + v * plotW;
    const y = v => pad.t + (1 - v) * plotH;

    const ticks = [0, 0.25, 0.5, 0.75, 1];
    let grid = ticks.map(t => `
      <line class="grid-line" x1="${x(t)}" x2="${x(t)}" y1="${pad.t}" y2="${h - pad.b}"/>
      <line class="grid-line" x1="${pad.l}" x2="${w - pad.r}" y1="${y(t)}" y2="${y(t)}"/>
      <text class="axis-label" x="${x(t)}" y="${h - pad.b + 16}" text-anchor="middle">${t}</text>
      <text class="axis-label" x="${pad.l - 8}" y="${y(t) + 3}" text-anchor="end">${t}</text>
    `).join("");

    const dots = data.map((d, i) => `
      <circle class="dot" data-i="${i}" cx="${x(d.dance)}" cy="${y(d.energy)}" r="5"></circle>
    `).join("");

    svg.innerHTML = `
      ${grid}
      <text class="axis-label" x="${pad.l + plotW / 2}" y="${h - 6}" text-anchor="middle">dancabilidade &rarr;</text>
      <text class="axis-label" x="${-(pad.t + plotH / 2)}" y="12" text-anchor="middle" transform="rotate(-90)">energia &rarr;</text>
      ${dots}`;

    const tooltip = document.getElementById("scatterTooltip");
    const wrap = document.getElementById("scatterWrap");
    svg.querySelectorAll(".dot").forEach((dot, i) => {
      const d = data[i];
      dot.addEventListener("mousemove", (e) => {
        const r = wrap.getBoundingClientRect();
        tooltip.style.left = (e.clientX - r.left) + "px";
        tooltip.style.top = (e.clientY - r.top) + "px";
        tooltip.innerHTML = `<strong>${d.g}</strong>
          <div class="row"><span>dancabilidade</span><span>${fmt2(d.dance)}</span></div>
          <div class="row"><span>energia</span><span>${fmt2(d.energy)}</span></div>
          <div class="row"><span>popularidade</span><span>${fmt1(d.pop)}</span></div>`;
        tooltip.classList.add("show");
        dot.classList.add("active");
      });
      dot.addEventListener("mouseleave", () => {
        tooltip.classList.remove("show");
        dot.classList.remove("active");
      });
    });
  })();

  const columns = [
    { key: "g", label: "Genero", fmt: v => v, align: "left" },
    { key: "n", label: "Faixas", fmt: v => v.toLocaleString("pt-BR") },
    { key: "pop", label: "Popularidade", fmt: fmt1 },
    { key: "dance", label: "Dancabilidade", fmt: fmt2 },
    { key: "energy", label: "Energia", fmt: fmt2 },
    { key: "tempo", label: "Tempo (bpm)", fmt: fmt1 },
    { key: "valence", label: "Valencia", fmt: fmt2 },
    { key: "acoustic", label: "Acustica", fmt: fmt2 },
  ];

  let sortKey = "pop", sortAsc = false;

  function renderTable() {
    const head = document.getElementById("tableHead");
    head.innerHTML = columns.map(c => `
      <th class="${c.key === sortKey ? "sorted" : ""}" style="text-align:${c.align || "right"}">
        <button data-key="${c.key}">${c.label}<span class="arrow">${sortKey === c.key ? (sortAsc ? "▲" : "▼") : "▼"}</span></button>
      </th>`).join("");

    head.querySelectorAll("button").forEach(btn => {
      btn.addEventListener("click", () => {
        const key = btn.dataset.key;
        if (key === sortKey) { sortAsc = !sortAsc; } else { sortKey = key; sortAsc = key === "g"; }
        renderTable();
      });
    });

    const sorted = [...data].sort((a, b) => {
      const av = a[sortKey], bv = b[sortKey];
      const cmp = typeof av === "string" ? av.localeCompare(bv) : av - bv;
      return sortAsc ? cmp : -cmp;
    });

    document.getElementById("tableBody").innerHTML = sorted.map(d => `
      <tr>${columns.map(c => `<td style="text-align:${c.align || "right"}">${c.fmt(d[c.key])}</td>`).join("")}</tr>
    `).join("");
  }

  renderTable();
</script>
{% endblock %}
```

- [ ] **Step 4: Create `site/static/style.css`**

```css
:root {
  color-scheme: light;
  --bg: #f6f4ee;
  --surface: #ffffff;
  --surface-2: #edeadf;
  --ink: #17150f;
  --ink-2: #5c584c;
  --ink-3: #8d8879;
  --border: rgba(23, 21, 15, 0.11);
  --border-strong: rgba(23, 21, 15, 0.22);
  --accent-450: #2a78d6;
  --accent-400: #3987e5;
  --accent-700: #0d366b;
  --grid-line: #e2dfd2;
  --row-hover: #f1eee2;
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --bg: #131210;
    --surface: #1c1b17;
    --surface-2: #24221d;
    --ink: #f4f2ea;
    --ink-2: #bcb7a6;
    --ink-3: #8d8879;
    --border: rgba(255, 255, 255, 0.10);
    --border-strong: rgba(255, 255, 255, 0.20);
    --accent-450: #5a9eec;
    --accent-400: #3987e5;
    --accent-700: #b7d3f6;
    --grid-line: #322f28;
    --row-hover: #26241e;
  }
}

:root[data-theme="dark"] {
  color-scheme: dark;
  --bg: #131210;
  --surface: #1c1b17;
  --surface-2: #24221d;
  --ink: #f4f2ea;
  --ink-2: #bcb7a6;
  --ink-3: #8d8879;
  --border: rgba(255, 255, 255, 0.10);
  --border-strong: rgba(255, 255, 255, 0.20);
  --accent-450: #5a9eec;
  --accent-400: #3987e5;
  --accent-700: #b7d3f6;
  --grid-line: #322f28;
  --row-hover: #26241e;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: "Source Sans 3", system-ui, -apple-system, "Segoe UI", sans-serif;
  -webkit-font-smoothing: antialiased;
}

.site { display: flex; flex-direction: column; min-height: 100vh; }
.site-main { flex: 1; }

.site-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border);
}

.site-nav-brand {
  font-family: "Manrope", sans-serif;
  font-weight: 800;
  color: var(--ink);
  text-decoration: none;
  font-size: 15px;
}

.site-nav-link {
  color: var(--ink-2);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
}

.site-nav-link:hover { color: var(--accent-450); }

.site-footer {
  padding: 24px;
  text-align: center;
  font-size: 12.5px;
  color: var(--ink-3);
}

.site-footer a { color: var(--accent-450); }

h1, h2 {
  font-family: "Manrope", system-ui, sans-serif;
  letter-spacing: -0.01em;
  text-wrap: balance;
  margin: 0;
}

.eyebrow {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: var(--accent-450);
  margin: 0 0 10px;
}

.hub-header, .page {
  max-width: 1080px;
  margin: 0 auto;
  padding: 56px 24px 8px;
}

.hub-header h1, .page > header h1 {
  font-size: clamp(30px, 4.2vw, 42px);
  font-weight: 800;
  color: var(--ink);
}

.hub-header p, .page > header p {
  max-width: 62ch;
  margin: 14px 0 0;
  color: var(--ink-2);
  font-size: 16px;
  line-height: 1.6;
}

.card-grid {
  max-width: 1080px;
  margin: 24px auto 80px;
  padding: 0 24px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}

.card {
  display: block;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 22px;
  text-decoration: none;
  color: inherit;
  transition: border-color 0.15s ease;
}

.card:hover { border-color: var(--accent-450); }
.card h2 { font-size: 18px; font-weight: 700; margin: 0 0 8px; }
.card p { margin: 0; color: var(--ink-2); font-size: 14px; line-height: 1.5; }

.page {
  display: flex;
  flex-direction: column;
  gap: 48px;
  padding-bottom: 80px;
}

.tiles {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 12px;
}

.tile {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px 18px;
}

.tile-label {
  font-size: 12px;
  color: var(--ink-3);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.tile-value {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 26px;
  font-weight: 600;
  color: var(--ink);
  margin-top: 6px;
  font-variant-numeric: tabular-nums;
}

.tile-sub { font-size: 13px; color: var(--ink-2); margin-top: 3px; }

section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 26px 26px 22px;
}

section > h2 { font-size: 19px; font-weight: 700; }
section > .section-sub { margin: 6px 0 20px; color: var(--ink-2); font-size: 14px; }

.chart-wrap { position: relative; overflow-x: auto; }
svg text { font-family: "Source Sans 3", sans-serif; }
.axis-label { fill: var(--ink-3); font-size: 10.5px; }
.genre-label { fill: var(--ink-2); font-size: 12px; }

.value-label {
  fill: var(--ink);
  font-size: 11.5px;
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-variant-numeric: tabular-nums;
}

.bar-row rect.hit { fill: transparent; }
.bar-row rect.bar { fill: var(--accent-450); transition: fill 0.12s ease; }
.bar-row:hover rect.bar { fill: var(--accent-400); }
.bar-row:hover rect.hit { fill: var(--row-hover); }

.grid-line { stroke: var(--grid-line); stroke-width: 1; }
.axis-line { stroke: var(--border-strong); stroke-width: 1; }

.dot {
  fill: var(--accent-450);
  fill-opacity: 0.82;
  stroke: var(--surface);
  stroke-width: 1.5;
  transition: fill-opacity 0.12s ease;
}

.dot:hover, .dot.active { fill-opacity: 1; stroke: var(--accent-700); }

.tooltip {
  position: absolute;
  pointer-events: none;
  background: var(--ink);
  color: var(--bg);
  font-size: 12.5px;
  line-height: 1.5;
  border-radius: 8px;
  padding: 9px 12px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.18);
  opacity: 0;
  transform: translate(-50%, calc(-100% - 10px));
  transition: opacity 0.1s ease;
  white-space: nowrap;
  z-index: 5;
}

.tooltip.show { opacity: 1; }
.tooltip strong { font-family: "Manrope", sans-serif; }
.tooltip .row { display: flex; justify-content: space-between; gap: 14px; }
.tooltip .row span:last-child { font-family: "IBM Plex Mono", monospace; font-variant-numeric: tabular-nums; }

.export-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
  margin-top: 12px;
}

.export-grid figure { margin: 0; }

.export-grid img {
  width: 100%;
  height: auto;
  border-radius: 8px;
  border: 1px solid var(--border);
  display: block;
}

.export-grid figcaption { margin-top: 8px; font-size: 13px; color: var(--ink-2); }

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13.5px;
  min-width: 760px;
}

th, td {
  text-align: right;
  padding: 9px 12px;
  border-bottom: 1px solid var(--border);
  font-variant-numeric: tabular-nums;
  font-family: "IBM Plex Mono", ui-monospace, monospace;
}

th:first-child, td:first-child {
  text-align: left;
  font-family: "Source Sans 3", sans-serif;
  color: var(--ink);
}

th {
  font-family: "Source Sans 3", sans-serif;
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--ink-3);
  position: sticky;
  top: 0;
  background: var(--surface);
}

th button { all: unset; cursor: pointer; display: inline-flex; align-items: center; gap: 4px; }
th button:focus-visible { outline: 2px solid var(--accent-450); outline-offset: 2px; border-radius: 3px; }
th .arrow { opacity: 0; font-size: 10px; }
th.sorted .arrow { opacity: 1; color: var(--accent-450); }
tbody tr:hover td { background: var(--row-hover); }

.table-wrap {
  overflow-x: auto;
  max-height: 460px;
  overflow-y: auto;
  border: 1px solid var(--border);
  border-radius: 8px;
}

@media (prefers-reduced-motion: reduce) {
  * { transition: none !important; }
}
```

- [ ] **Step 5: Commit**

```bash
git add site/templates site/static
git commit -m "$(cat <<'EOF'
Add site templates and shared stylesheet

base.html holds nav/footer/tokens; index.html is the analyses hub;
genero.html ports the genre dashboard (bars, scatter, sortable
table, PNG export section) to read its data from a Jinja2 variable
instead of a hand-written array.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Wire up `build_site.py` end-to-end and verify locally

**Files:**
- Modify: `site/build_site.py`

- [ ] **Step 1: Add rendering and asset copying to `site/build_site.py`**

Replace the file's full contents with:

```python
"""Builds the static GitHub Pages site into site/dist/."""

import json
import shutil
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SITE_DIR / "templates"
STATIC_DIR = SITE_DIR / "static"
DIST_DIR = SITE_DIR / "dist"

GENRE_CSV = ROOT / "occurrences_by_genre.csv"
GENRE_PNGS = [ROOT / "genre_popularity.png", ROOT / "genre_energy_dance.png"]

ANALYSES = [
    {
        "id": "genero",
        "title": "Perfil dos Generos",
        "description": "Popularidade e caracteristicas de audio por genero musical.",
        "href": "genero.html",
    },
]


def load_genre_rows(csv_path: Path) -> list[dict]:
    """Read occurrences_by_genre.csv into the compact row shape the dashboard needs."""
    df = pd.read_csv(csv_path)
    rows = []
    for _, row in df.iterrows():
        rows.append(
            {
                "g": row["track_genre"],
                "n": int(row["contagem"]),
                "pop": round(float(row["popularity"]), 1),
                "dance": round(float(row["danceability"]), 3),
                "energy": round(float(row["energy"]), 3),
                "tempo": round(float(row["tempo"]), 1),
                "valence": round(float(row["valence"]), 3),
                "acoustic": round(float(row["acousticness"]), 3),
            }
        )
    return rows


def rows_to_embeddable_json(rows: list[dict]) -> str:
    """JSON-encode rows for embedding in a <script> tag, safe against '</script>'."""
    return json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")


def build() -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)

    index_html = env.get_template("index.html").render(title="Analises", analyses=ANALYSES)
    (DIST_DIR / "index.html").write_text(index_html, encoding="utf-8")

    rows = load_genre_rows(GENRE_CSV)
    genero_html = env.get_template("genero.html").render(
        title="Perfil dos Generos",
        rows_json=rows_to_embeddable_json(rows),
    )
    (DIST_DIR / "genero.html").write_text(genero_html, encoding="utf-8")

    shutil.copytree(STATIC_DIR, DIST_DIR / "static")
    for png in GENRE_PNGS:
        shutil.copy(png, DIST_DIR / png.name)

    print(f"Site gerado em {DIST_DIR}")


if __name__ == "__main__":
    build()
```

- [ ] **Step 2: Run the existing tests to confirm the loader still passes**

Run: `source .venv/Scripts/activate && python -m pytest tests/ -v`
Expected: all tests pass (chart_style + build_site loader tests).

- [ ] **Step 3: Run the full pipeline and verify the site builds**

Run:
```bash
source .venv/Scripts/activate
python group_occurrences.py
python plot_genre_charts.py
python site/build_site.py
```
Expected: last line `Site gerado em .../site/dist`, and these files exist:
`site/dist/index.html`, `site/dist/genero.html`, `site/dist/static/style.css`,
`site/dist/genre_popularity.png`, `site/dist/genre_energy_dance.png`.

Run this sanity check for unresolved Jinja2 syntax (would indicate a template
rendering bug):
```bash
grep -c "{{" site/dist/index.html site/dist/genero.html
```
Expected: `0` for both files (no literal `{{` should remain after rendering).

- [ ] **Step 4: Open the site in a browser and check it visually**

```bash
start site/dist/index.html
```
(On Windows this opens the default browser via the `start` command run through
git-bash; use `Start-Process site/dist/index.html` if running this step in
PowerShell instead.)

Confirm:
- `index.html` shows the nav, hub header, and one card ("Perfil dos Generos")
  linking to `genero.html`.
- `genero.html` shows the 4 stat tiles, the ranked bar chart, the scatter plot
  with working hover tooltips, the two exported PNGs, and the sortable table
  (click a header, confirm the sort order changes).
- Toggling OS dark mode switches the page to the dark palette without any
  unstyled/invisible text.

- [ ] **Step 5: Commit**

```bash
git add site/build_site.py
git commit -m "$(cat <<'EOF'
Render the analyses site from templates and CSV data

build_site.py now renders index.html and genero.html via Jinja2 and
copies static assets + chart PNGs into site/dist/, the directory the
GitHub Actions workflow will publish.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: GitHub Actions deploy workflow

**Files:**
- Create: `.github/workflows/pages.yml`

- [ ] **Step 1: Write the workflow**

```yaml
name: Deploy analyses site to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: python group_occurrences.py
      - run: python plot_genre_charts.py
      - run: python site/build_site.py
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site/dist

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 2: Validate the YAML parses**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/pages.yml')); print('valid')"`
Expected: `valid`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/pages.yml
git commit -m "$(cat <<'EOF'
Add GitHub Actions workflow to deploy the analyses site

Runs the grouping/plotting/build pipeline on every push to main and
publishes site/dist/ to GitHub Pages via the official Pages actions.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 8: Push and enable GitHub Pages (requires explicit confirmation)

**This task is not autonomous.** It pushes to `origin/main` and changes the
repository's GitHub Pages settings — both are actions on shared state. Confirm
with the user before running any command below.

- [ ] **Step 1: Confirm with the user, then push**

```bash
git push origin main
```

- [ ] **Step 2: Confirm with the user, then set the Pages source to "GitHub Actions"**

This is a one-time repo-settings change (idempotent if run again):

```bash
gh api -X PUT repos/Lucas-AV/Grupo-8-ResIA/pages -f build_type=workflow
```

If the repo has no Pages site yet, this call creates one with the Actions
build type in a single step; if a Pages site already exists with a different
source, this switches it to Actions.

- [ ] **Step 3: Watch the workflow run**

```bash
gh run watch
```

Expected: both the `build` and `deploy` jobs finish with a green check. The
`deploy` job's log prints the live Pages URL
(`https://lucas-av.github.io/Grupo-8-ResIA/`).

- [ ] **Step 4: Open the published URL and repeat the Task 6 Step 4 visual checks against it**

Confirm the live site matches what was checked locally: nav, hub card, stat
tiles, both charts with tooltips, PNG export section, sortable table, and
correct rendering in both light and dark OS themes.
