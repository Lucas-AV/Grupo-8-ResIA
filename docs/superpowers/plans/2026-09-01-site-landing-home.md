# Landing Home Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `site/templates/index.html` from a bare card grid into a landing page — hero, headline stats, team, then the existing analyses card grid — using the corrected dataset numbers (31.819 faixas, 32 gêneros).

**Architecture:** `site/build_site.py` gains a shared `load_dataset_profile()` helper (used by the existing `load_profile_tiles` and a new `load_home_tiles`), a `TEAM` constant, and passes `team`/`tiles` into the `index.html` render. `site/templates/index.html` gains three new blocks (hero, tiles, team) above the unchanged card grid. `site/static/style.css` gains new classes only (`.hero`, `.hero-actions`, `.btn`/`.btn-primary`/`.btn-secondary`, `.home-tiles`, `.team-section`, `.team-grid`, `.team-member`) — nothing existing is edited.

**Tech Stack:** Python 3, pandas, Jinja2, pytest (existing stack — no new dependencies).

Reference spec: `docs/superpowers/specs/2026-09-01-site-landing-home-design.md`

---

### Task 1: Shared `load_dataset_profile` helper

**Files:**
- Modify: `site/build_site.py:139-155` (the `load_profile_tiles` function)
- Test: `tests/test_build_site.py`

`load_profile_tiles` currently opens `dataset_profile.json` itself. Extracting the
open+parse into its own function lets `load_home_tiles` (Task 2) and `build()`'s
`total_tracks_display` line (Task 3) reuse it instead of duplicating
`json.load(open(...))`.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_build_site.py` (append at the end of the file):

```python
def test_load_dataset_profile_parses_json(tmp_path):
    profile_path = tmp_path / "dataset_profile.json"
    profile_path.write_text(
        json.dumps({"total_tracks": 5, "unique_genres": 2}),
        encoding="utf-8",
    )

    profile = load_dataset_profile(profile_path)

    assert profile == {"total_tracks": 5, "unique_genres": 2}
```

Update the import line at the top of `tests/test_build_site.py` from:

```python
from build_site import load_genre_rows, load_profile_tiles, load_table_rows
```

to:

```python
from build_site import (
    load_dataset_profile,
    load_genre_rows,
    load_profile_tiles,
    load_table_rows,
)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_build_site.py -v`
Expected: `ImportError: cannot import name 'load_dataset_profile'`

- [ ] **Step 3: Add `load_dataset_profile` and refactor `load_profile_tiles`**

In `site/build_site.py`, replace the existing `load_profile_tiles` function
(currently lines 139-155):

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
```

with:

```python
def load_dataset_profile(profile_path: Path) -> dict:
    """Parse dataset_profile.json once; shared by the home tiles and the overview page."""
    with open(profile_path, encoding="utf-8") as f:
        return json.load(f)


def load_profile_tiles(profile_path: Path) -> list[dict]:
    """Turn dataset_profile.json into the tile list visao-geral.html renders."""
    profile = load_dataset_profile(profile_path)
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_build_site.py -v`
Expected: all tests pass, including the two pre-existing `load_profile_tiles`
tests (behavior is unchanged) and the new `load_dataset_profile` test.

- [ ] **Step 5: Commit**

```bash
git add site/build_site.py tests/test_build_site.py
git commit -m "$(cat <<'EOF'
Extract load_dataset_profile helper from load_profile_tiles

Shares the dataset_profile.json parse with the upcoming landing-page
tiles instead of duplicating json.load(open(...)).

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: `TEAM` constant and `load_home_tiles`

**Files:**
- Modify: `site/build_site.py` (add constant + function)
- Test: `tests/test_build_site.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_build_site.py`:

```python
def test_load_home_tiles_combines_dataset_and_market_numbers(tmp_path):
    profile_path = tmp_path / "dataset_profile.json"
    profile_path.write_text(
        json.dumps({"total_tracks": 31819, "unique_genres": 32}),
        encoding="utf-8",
    )

    tiles = load_home_tiles(profile_path)

    assert tiles == [
        {"label": "Faixas analisadas", "value": "31.819"},
        {"label": "Generos", "value": "32"},
        {"label": "Crescimento Brasil (2025)", "value": "+14,1%", "sub": "vs +6,4% global"},
        {"label": "Mercado global 2025", "value": "US$ 31,7bi", "sub": "IFPI 2026"},
    ]
```

Update the import line at the top of `tests/test_build_site.py` to add
`load_home_tiles`:

```python
from build_site import (
    load_dataset_profile,
    load_genre_rows,
    load_home_tiles,
    load_profile_tiles,
    load_table_rows,
)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_build_site.py -v`
Expected: `ImportError: cannot import name 'load_home_tiles'`

- [ ] **Step 3: Add `TEAM` and `load_home_tiles` to `site/build_site.py`**

Insert the `TEAM` constant right after the `MARKET_PNGS` list (currently ends
at line 37, right before `ANALYSES = [` on line 39):

```python
TEAM = [
    {"name": "Lucas Alves Vilela", "github": "Lucas-AV"},
    {"name": "Dayane Ferreira", "github": "dayarierref"},
    {"name": "Eduarda Reis", "github": "dudsstar16"},
    {"name": "Ruan Sobreira Carvalho", "github": "Ruan-Carvalho"},
    {"name": "femathrl0", "github": "femathrl0"},
]
```

Add `load_home_tiles` right after `load_dataset_profile` (which Task 1 placed
directly above `load_profile_tiles`):

```python
def load_home_tiles(profile_path: Path) -> list[dict]:
    """Headline stats for the landing page: dataset size + curated market numbers."""
    profile = load_dataset_profile(profile_path)
    return [
        {"label": "Faixas analisadas", "value": f"{profile['total_tracks']:,}".replace(",", ".")},
        {"label": "Generos", "value": str(profile["unique_genres"])},
        {"label": "Crescimento Brasil (2025)", "value": "+14,1%", "sub": "vs +6,4% global"},
        {"label": "Mercado global 2025", "value": "US$ 31,7bi", "sub": "IFPI 2026"},
    ]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_build_site.py -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add site/build_site.py tests/test_build_site.py
git commit -m "$(cat <<'EOF'
Add TEAM constant and load_home_tiles for the landing page

load_home_tiles mixes the dataset_profile.json numbers with the same
curated market figures already hardcoded for mercado.html's tiles.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Wire hero/tiles/team into `index.html`'s render

**Files:**
- Modify: `site/build_site.py:181-196` (the start of `build()`)
- Modify: `site/build_site.py:211-213` (the `total_tracks_display` block)

No new test here — `build()` is exercised end-to-end by manually running the
pipeline in Task 5 (consistent with how the original site build was verified;
see `docs/superpowers/specs/2026-08-27-github-pages-site-design.md`).

- [ ] **Step 1: Update the `index.html` render call**

In `site/build_site.py`, inside `build()`, replace:

```python
    index_html = env.get_template("index.html").render(title="Analises", analyses=ANALYSES)
    (DIST_DIR / "index.html").write_text(index_html, encoding="utf-8")
```

with:

```python
    index_html = env.get_template("index.html").render(
        title="Analises",
        analyses=ANALYSES,
        team=TEAM,
        tiles=load_home_tiles(PROFILE_JSON),
    )
    (DIST_DIR / "index.html").write_text(index_html, encoding="utf-8")
```

- [ ] **Step 2: Reuse `load_dataset_profile` for `total_tracks_display`**

Further down in `build()`, replace:

```python
    with open(PROFILE_JSON, encoding="utf-8") as f:
        total_tracks_display = f"{json.load(f)['total_tracks']:,}".replace(",", ".")
```

with:

```python
    total_tracks_display = f"{load_dataset_profile(PROFILE_JSON)['total_tracks']:,}".replace(",", ".")
```

- [ ] **Step 3: Commit**

```bash
git add site/build_site.py
git commit -m "$(cat <<'EOF'
Pass team and headline tiles into the index.html render

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Hero, tiles, and team markup in `index.html`

**Files:**
- Modify: `site/templates/index.html` (full rewrite)

- [ ] **Step 1: Replace `site/templates/index.html`**

Current content:

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

Replace it with:

```html
{% extends "base.html" %}
{% block content %}
<div class="hero">
  <p class="eyebrow">Grupo 8 &middot; ResIA</p>
  <h1>De Dados a Recomendacoes</h1>
  <p>Analisando 31.819 faixas do Spotify em 32 generos para construir um
    agente de recomendacao de musicas e playlists.</p>
  <div class="hero-actions">
    <a class="btn btn-primary" href="#analises">Ver analises</a>
    <a class="btn btn-secondary" href="https://github.com/Lucas-AV/Grupo-8-ResIA">Ver no GitHub &#8599;</a>
  </div>
</div>

<div class="tiles home-tiles">
  {% for tile in tiles %}
  <div class="tile">
    <div class="tile-label">{{ tile.label }}</div>
    <div class="tile-value">{{ tile.value }}</div>
    {% if tile.sub %}<div class="tile-sub">{{ tile.sub }}</div>{% endif %}
  </div>
  {% endfor %}
</div>

<div class="team-section">
  <h2>Equipe</h2>
  <div class="team-grid">
    {% for member in team %}
    <a class="team-member" href="https://github.com/{{ member.github }}">
      <img src="https://github.com/{{ member.github }}.png" alt="{{ member.name }}" loading="lazy">
      <span>{{ member.name }}</span>
    </a>
    {% endfor %}
  </div>
</div>

<header class="hub-header" id="analises">
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

Note: `.hero` and `.team-section` are plain `<div>`s, not `<section>` — the
existing stylesheet has a bare `section { background: var(--surface); border:
1px solid var(--border); ... }` rule (for the analysis-page cards in
`analise.html`) that would otherwise apply unwanted card styling to the hero
and team blocks.

- [ ] **Step 2: Commit**

```bash
git add site/templates/index.html
git commit -m "$(cat <<'EOF'
Add hero, headline tiles, and team sections to index.html

index.html goes from a bare card grid to a landing page: hero with
two CTAs, 4 headline stat tiles, a team grid, then the existing
analyses card grid (now anchored at #analises).

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Styling for the new sections

**Files:**
- Modify: `site/static/style.css` (append new rules)

- [ ] **Step 1: Append the new rules to `site/static/style.css`**

Add at the end of the file:

```css
.hero {
  max-width: 1080px;
  margin: 0 auto;
  padding: 64px 24px 16px;
}

.hero h1 {
  font-size: clamp(32px, 5vw, 48px);
  font-weight: 800;
  color: var(--ink);
}

.hero > p {
  max-width: 62ch;
  margin: 16px 0 0;
  color: var(--ink-2);
  font-size: 17px;
  line-height: 1.6;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 28px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 11px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  transition: opacity 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}

.btn-primary { background: var(--accent-450); color: #fff; }
.btn-primary:hover { opacity: 0.88; }

.btn-secondary {
  background: transparent;
  color: var(--ink);
  border: 1px solid var(--border-strong);
}

.btn-secondary:hover { border-color: var(--accent-450); color: var(--accent-450); }

.home-tiles {
  max-width: 1080px;
  margin: 8px auto 0;
  padding: 0 24px;
}

.team-section {
  max-width: 1080px;
  margin: 8px auto 0;
  padding: 40px 24px 8px;
}

.team-section h2 {
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 20px;
}

.team-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 16px;
}

.team-member {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 16px;
  border-radius: 12px;
  text-decoration: none;
  color: inherit;
  transition: background 0.15s ease;
}

.team-member:hover { background: var(--surface); }

.team-member img {
  width: 84px;
  height: 84px;
  border-radius: 50%;
  border: 2px solid var(--border);
}

.team-member span {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--ink);
  text-align: center;
}
```

- [ ] **Step 2: Commit**

```bash
git add site/static/style.css
git commit -m "$(cat <<'EOF'
Style the landing page hero, tiles, and team sections

New classes only (.hero, .btn*, .home-tiles, .team-*) — nothing
existing in style.css changes.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Build, verify locally, and push

**Files:** none (verification + deploy only)

- [ ] **Step 1: Run the full test suite**

Run: `python -m pytest tests/ -v`
Expected: all tests pass.

- [ ] **Step 2: Build the site**

Run: `python site/build_site.py`
Expected: `Site gerado em .../site/dist` with no errors.

- [ ] **Step 3: Open and visually check `site/dist/index.html`**

```bash
start site/dist/index.html
```
(On Windows via git-bash; use `Start-Process site/dist/index.html` in
PowerShell.)

Confirm:
- Hero renders with headline, subtitle, and both buttons; "Ver analises"
  scrolls down to the card grid; "Ver no GitHub" opens the repo in a new
  context (same tab is fine — no `target="_blank"` needed for a same-site
  page).
- 4 headline tiles show: faixas analisadas (31.819), generos (32),
  crescimento Brasil (+14,1%), mercado global (US$ 31,7bi).
- 5 team members render with circular avatars loading correctly and each
  links to the right GitHub profile.
- Card grid below still shows all 6 analyses, unchanged.
- Toggle OS dark mode: hero, tiles, team, and buttons all stay legible (no
  invisible text, no unstyled flash).

- [ ] **Step 4: Confirm with the user, then push**

```bash
git push origin main
```

- [ ] **Step 5: Confirm with the user, then watch the deploy workflow**

```bash
gh run watch
```

Expected: both `build` and `deploy` jobs finish green. Open
`https://lucas-av.github.io/Grupo-8-ResIA/` and repeat the Step 3 checks
against the live site.
