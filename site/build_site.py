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
    {
        "id": "modo",
        "title": "Escala por Genero",
        "description": "Proporcao de faixas em escala maior vs. menor, por genero.",
        "href": "modo.html",
    },
    {
        "id": "popularidade",
        "title": "Popularidade x Catalogo do Artista",
        "description": "Popularidade media da faixa conforme o numero de faixas do artista na base.",
        "href": "popularidade.html",
    },
]

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

    shutil.copytree(STATIC_DIR, DIST_DIR / "static")
    all_pngs = GENRE_PNGS + [
        fig["path"] for analysis in STATIC_ANALYSES for fig in analysis["figures"]
    ]
    for png in all_pngs:
        shutil.copy(png, DIST_DIR / png.name)

    print(f"Site gerado em {DIST_DIR}")


if __name__ == "__main__":
    build()
