# Landing page redesign — report-style visual language

## Context

The landing page (`site/templates/index.html`, `site/static/style.css`) shipped
recently: hero + headline tiles + team grid + analyses card grid. The team also
just published a market-analysis report/pitch as `mercado.html` and as a PDF
(`analise_mercado_streaming/relatorio-sinal-do-streaming.pdf`, source artifact
"Sinal do Streaming"). That report has a distinct, more "presentable" visual
language: a big condensed all-caps display title, a small monospace masthead
line above it, a colored accent rule under the title, and caps section
headings prefixed with a small numbered badge (`01`, `02`, ...).

Goal: bring that visual language into the landing page's hero and section
headings, without touching the report's own page (`mercado.html`) or any of
the other 5 analysis pages, and without changing the site's shared blue accent
color — this is a typography/layout treatment, not a rebrand.

## Non-goals

- No change to `mercado.html`, `genero.html`, or the `analise.html`-rendered
  pages (`modo`, `popularidade`, `visao-geral`, `correlacoes`) — same scope
  boundary the original landing-page spec used.
- No new accent color — stays `var(--accent-450)` (blue), not the report's
  warm gold/orange.
- No change to the team grid or card grid markup/styling — only the hero and
  the three section headings (`Destaques`, `Equipe`, `Analises`) change.

## Font

Add **Anton** (Google Fonts, single weight 400 — the face is already
visually black/bold) for the hero `<h1>` only. Everything else keeps the
existing Manrope / Source Sans 3 / IBM Plex Mono stack. `site/templates/base.html`'s
existing single Google Fonts request gains `family=Anton` alongside the
current families (still one `<link>`, no extra HTTP request):

```
https://fonts.googleapis.com/css2?family=Anton&family=Manrope:wght@600;700;800&family=Source+Sans+3:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap
```

## Hero changes (`site/templates/index.html`, `site/static/style.css`)

- Replace the hero's current `<p class="eyebrow">Grupo 8 &middot; ResIA</p>`
  with a fuller masthead line, new class `.hero-meta` (monospace, uppercase,
  `--ink-3`, smaller than the old eyebrow): `Grupo 8 &middot; Residencia em IA
  (UnB / LabLivre / Instituto Eldorado) &middot; Agosto 2026`.
- `<h1>De Dados a Recomendacoes</h1>` — restyle the *existing* `.hero h1` rule
  (added in the previous landing-page work) to use Anton, uppercase, larger:
  `font-family: "Anton", "Manrope", system-ui, sans-serif; font-weight: 400;
  text-transform: uppercase; font-size: clamp(36px, 6vw, 64px); line-height:
  1.05;` (drops the old `font-weight: 800` — Anton doesn't need it).
- New `<div class="hero-rule"></div>` immediately after the `<h1>`, before the
  subtitle `<p>` — a short accent bar (not a full-width divider): `width:
  64px; height: 4px; background: var(--accent-450); border-radius: 2px;
  margin: 18px 0 0;`.
- Subtitle `<p>` and `.hero-actions` buttons: unchanged.

## Numbered section headings (new `.section-heading` component)

A small reusable block: a square number badge (accent-450 background, reusing
the existing `--on-accent` token for text color — the same token added to fix
the primary button's dark-mode contrast) followed by an `<h2>`.

```html
<div class="section-heading">
  <span class="section-number">01</span>
  <h2>Destaques</h2>
</div>
```

Applied three times, replacing the current plain/missing headings:

1. **Destaques** (currently has no heading at all — the tiles div is
   unlabeled): add this heading immediately before `<div class="tiles
   home-tiles">`, itself wrapped with the `.home-tiles` class (reusing the
   existing container-width rule, not a new one) so it lines up with the
   tiles below it. Number: `01`.
2. **Equipe**: replace the current bare `<h2>Equipe</h2>` inside
   `.team-section` with the `.section-heading` block. Number: `02`.
3. **Analises**: inside the existing `<header class="hub-header"
   id="analises">`, replace `<h1>Analises</h1>` with the `.section-heading`
   block (`<h2>Analises</h2>`). Number: `03`. This also fixes a pre-existing
   minor issue flagged in the original landing-page code review: the page had
   two `<h1>` elements (hero + this one); after this change there's exactly
   one `<h1>` on the page (the hero).

CSS: new `.section-heading` (flex row, `gap: 12px`, `margin: 0 0 20px`),
`.section-number` (28×28px, `border-radius: 6px`, `background:
var(--accent-450)`, `color: var(--on-accent)`, IBM Plex Mono 12px/600), and
`.section-heading h2` (22px/700/`var(--ink)`, `margin: 0` — this replaces the
old dedicated `.team-section h2` rule, which is deleted since every `<h2>` in
these three spots is now wrapped identically).

## Testing / verification

- No automated test coverage for template/CSS output, consistent with how
  the original landing-page and site-build specs treated
  `templates/`/`static/` changes.
- Build locally (`python site/build_site.py`), open `site/dist/index.html`:
  confirm the hero title renders in the new display font in uppercase, the
  accent rule appears under the title, the masthead line reads correctly,
  and all three sections (`Destaques`, `Equipe`, `Analises`) show a numbered
  badge (`01`/`02`/`03`) beside their heading.
- Confirm exactly one `<h1>` remains on the rendered page
  (`grep -c "<h1" site/dist/index.html` → `1`).
- Toggle OS dark mode: hero title, accent rule, masthead line, and the three
  number badges all stay legible (the badge reuses `--on-accent`, already
  verified contrast-safe in both themes from the earlier `.btn-primary` fix).
- `python -m pytest -v` still passes (no test touches templates/CSS, so this
  just confirms nothing in `build_site.py` regressed).
