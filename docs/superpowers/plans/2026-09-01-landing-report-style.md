# Landing Page Report-Style Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restyle the landing page's hero (display font, masthead line, accent rule) and give its three sections (`Destaques`, `Equipe`, `Analises`) a numbered heading treatment, echoing the "Sinal do Streaming" report's visual language — without touching any other page or the shared blue accent color.

**Architecture:** `site/templates/base.html` gains one font family in its existing Google Fonts request. `site/templates/index.html` gets its hero markup extended (masthead line + accent-rule div) and three plain/missing headings replaced by a shared `.section-heading` block (number badge + `<h2>`). `site/static/style.css` restyles the existing `.hero h1` rule, adds `.hero-meta`/`.hero-rule`/`.section-heading`/`.section-number`, and removes the now-redundant `.team-section h2` rule.

**Tech Stack:** Jinja2 templates, plain CSS (existing design-token system) — no new dependencies, no Python changes.

Reference spec: `docs/superpowers/specs/2026-09-01-landing-report-style-design.md`

---

### Task 1: Add the Anton font

**Files:**
- Modify: `site/templates/base.html:9`

- [ ] **Step 1: Add `family=Anton` to the existing Google Fonts request**

In `site/templates/base.html`, line 9 currently reads:

```html
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@600;700;800&family=Source+Sans+3:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
```

Replace it with:

```html
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Manrope:wght@600;700;800&family=Source+Sans+3:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
```

(Anton ships one weight, 400 — no `:wght@` needed for it.)

- [ ] **Step 2: Commit**

```bash
git add site/templates/base.html
git commit -m "$(cat <<'EOF'
Add Anton font for the landing page hero title

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Hero markup — masthead line and accent rule

**Files:**
- Modify: `site/templates/index.html:3-12` (the `.hero` block)

- [ ] **Step 1: Update the hero block**

In `site/templates/index.html`, the current hero block reads:

```html
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
```

Replace it with:

```html
<div class="hero">
  <p class="hero-meta">Grupo 8 &middot; Residencia em IA (UnB / LabLivre / Instituto Eldorado) &middot; Agosto 2026</p>
  <h1>De Dados a Recomendacoes</h1>
  <div class="hero-rule"></div>
  <p>Analisando 31.819 faixas do Spotify em 32 generos para construir um
    agente de recomendacao de musicas e playlists.</p>
  <div class="hero-actions">
    <a class="btn btn-primary" href="#analises">Ver analises</a>
    <a class="btn btn-secondary" href="https://github.com/Lucas-AV/Grupo-8-ResIA">Ver no GitHub &#8599;</a>
  </div>
</div>
```

(The old `<p class="eyebrow">` is replaced by `<p class="hero-meta">` — `.eyebrow`
is still used elsewhere, e.g. `analise.html`'s pages, so it isn't removed from
`style.css`, just no longer used in this one spot.)

- [ ] **Step 2: Commit**

```bash
git add site/templates/index.html
git commit -m "$(cat <<'EOF'
Add hero masthead line and accent rule to index.html

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Numbered section headings in `index.html`

**Files:**
- Modify: `site/templates/index.html` (three spots: before the tiles, inside `.team-section`, inside the analises `<header>`)

Depends on Task 2 having already landed (same file, sequential edits avoid
merge conflicts within the plan).

- [ ] **Step 1: Add the "Destaques" heading before the tiles**

Currently (right after the `.hero` closing `</div>`):

```html
<div class="tiles home-tiles">
```

Replace with:

```html
<div class="section-heading home-tiles">
  <span class="section-number">01</span>
  <h2>Destaques</h2>
</div>
<div class="tiles home-tiles">
```

- [ ] **Step 2: Replace the "Equipe" heading**

Currently:

```html
<div class="team-section">
  <h2>Equipe</h2>
  <div class="team-grid">
```

Replace with:

```html
<div class="team-section">
  <div class="section-heading">
    <span class="section-number">02</span>
    <h2>Equipe</h2>
  </div>
  <div class="team-grid">
```

- [ ] **Step 3: Replace the "Analises" heading**

Currently:

```html
<header class="hub-header" id="analises">
  <p class="eyebrow">Dataset Spotify &middot; groupby</p>
  <h1>Analises</h1>
  <p>Exploracoes do dataset de faixas do Spotify, geradas automaticamente pelos
    scripts deste repositorio a cada atualizacao.</p>
</header>
```

Replace with:

```html
<header class="hub-header" id="analises">
  <p class="eyebrow">Dataset Spotify &middot; groupby</p>
  <div class="section-heading">
    <span class="section-number">03</span>
    <h2>Analises</h2>
  </div>
  <p>Exploracoes do dataset de faixas do Spotify, geradas automaticamente pelos
    scripts deste repositorio a cada atualizacao.</p>
</header>
```

(This header's own `.eyebrow` line — "Dataset Spotify · groupby" — is
untouched; only the `<h1>` becomes a `.section-heading`-wrapped `<h2>`. After
this change the page has exactly one `<h1>` left: the hero's.)

- [ ] **Step 4: Verify exactly one `<h1>` remains**

Run: `grep -c "<h1" site/templates/index.html`
Expected: `1`

- [ ] **Step 5: Commit**

```bash
git add site/templates/index.html
git commit -m "$(cat <<'EOF'
Add numbered section headings to Destaques, Equipe, and Analises

Also fixes the page having two <h1> elements (hero + this "Analises"
header) — the header's heading is now an <h2>, leaving one <h1>.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: CSS for the new hero/section-heading styles

**Files:**
- Modify: `site/static/style.css:358-362` (restyle `.hero h1`)
- Modify: `site/static/style.css:414-418` (remove `.team-section h2`, superseded)
- Modify: `site/static/style.css` (add `.hero-meta`, `.hero-rule`,
  `.section-heading`, `.section-number`, `.section-heading h2`)

- [ ] **Step 1: Restyle `.hero h1`**

Current (`site/static/style.css:358-362`):

```css
.hero h1 {
  font-size: clamp(32px, 5vw, 48px);
  font-weight: 800;
  color: var(--ink);
}
```

Replace with:

```css
.hero h1 {
  font-family: "Anton", "Manrope", system-ui, sans-serif;
  font-size: clamp(36px, 6vw, 64px);
  font-weight: 400;
  line-height: 1.05;
  text-transform: uppercase;
  color: var(--ink);
}
```

- [ ] **Step 2: Add `.hero-meta` and `.hero-rule`**

Add right before the `.hero h1` rule (i.e. between `.hero { ... }` and
`.hero h1 { ... }`):

```css
.hero-meta {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-3);
  margin: 0 0 14px;
}
```

Add right after the `.hero h1 { ... }` rule (before `.hero > p { ... }`):

```css
.hero-rule {
  width: 64px;
  height: 4px;
  background: var(--accent-450);
  border-radius: 2px;
  margin: 18px 0 0;
}
```

- [ ] **Step 3: Remove `.team-section h2` and add the shared `.section-heading` rules**

Current (`site/static/style.css:414-418`):

```css
.team-section h2 {
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 20px;
}
```

Delete this rule entirely. In its place (same location in the file), add:

```css
.section-heading {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 20px;
}

.section-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: var(--accent-450);
  color: var(--on-accent);
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.section-heading h2 {
  font-size: 22px;
  font-weight: 700;
  color: var(--ink);
  margin: 0;
}
```

- [ ] **Step 4: Commit**

```bash
git add site/static/style.css
git commit -m "$(cat <<'EOF'
Style the hero display title and numbered section headings

Restyles .hero h1 with the new Anton display font. Adds .hero-meta
(masthead line), .hero-rule (accent bar), and the shared
.section-heading/.section-number component used by Destaques,
Equipe, and Analises. Removes the now-redundant .team-section h2
rule (superseded by .section-heading h2).

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Build, verify, and push

**Files:** none (verification + deploy only)

- [ ] **Step 1: Run the test suite**

Run: `python -m pytest -v`
Expected: all tests pass (no test touches templates/CSS, this just confirms
nothing in `build_site.py` regressed).

- [ ] **Step 2: Build the site**

Run: `python site/build_site.py`
Expected: `Site gerado em .../site/dist` with no errors.

- [ ] **Step 3: Verify the `<h1>` count**

Run: `grep -c "<h1" site/dist/index.html`
Expected: `1`

- [ ] **Step 4: Open and visually check `site/dist/index.html`**

```bash
start site/dist/index.html
```
(git-bash on Windows; `Start-Process site/dist/index.html` in PowerShell.)

Confirm:
- Hero title renders in the new condensed display font, all caps.
- The masthead line ("Grupo 8 · Residencia em IA...") shows above the title
  in small monospace caps.
- A short blue accent bar appears directly under the title, above the
  subtitle paragraph.
- "Destaques", "Equipe", and "Analises" each show a small numbered badge
  (`01`, `02`, `03`) to the left of their heading, same blue as the primary
  button.
- Toggle OS dark mode: title, masthead line, accent bar, and all three
  number badges stay legible (no invisible text).
- The rest of the page (tiles, team grid, card grid) is visually unchanged
  from before this redesign.

- [ ] **Step 5: Confirm with the user, then push**

```bash
git push origin main
```

- [ ] **Step 6: Confirm with the user, then watch the deploy workflow**

```bash
gh run watch
```

Expected: both `build` and `deploy` jobs finish green. Open
`https://lucas-av.github.io/Grupo-8-ResIA/` and repeat the Step 4 checks
against the live site.
