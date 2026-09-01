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

PROFILE_JSON = ROOT / "dataset_profile.json"
MULTI_GENRE_CSV = ROOT / "dataset_multi_genre_tracks.csv"
ARTIST_DIST_PNG = ROOT / "artist_track_distribution.png"
ALBUM_DIST_PNG = ROOT / "album_track_distribution.png"

CORRELATIONS_CSV = ROOT / "correlations_top_pairs.csv"
CORRELATION_HEATMAP_PNG = ROOT / "correlation_heatmap.png"

MARKET_DIR = ROOT / "analise_mercado_streaming"
MARKET_SHARE_CSV = MARKET_DIR / "data" / "platform_market_share.csv"
MARKET_PNGS = [
    MARKET_DIR / "output_spotify_usuarios.png",
    MARKET_DIR / "output_spotify_receita.png",
    MARKET_DIR / "output_spotify_margem.png",
    MARKET_DIR / "output_mercado_global.png",
    MARKET_DIR / "output_assinantes_globais.png",
    MARKET_DIR / "output_brasil_vs_global.png",
    MARKET_DIR / "output_market_share.png",
]
MARKET_REPORT_PDF = MARKET_DIR / "relatorio-sinal-do-streaming.pdf"

TEAM = [
    {"name": "Lucas Alves Vilela", "github": "Lucas-AV"},
    {"name": "Dayane Ferreira", "github": "dayarierref"},
    {"name": "Eduarda Reis", "github": "dudsstar16"},
    {"name": "Ruan Sobreira Carvalho", "github": "Ruan-Carvalho"},
    {"name": "femathrl0", "github": "femathrl0"},
    {"name": "Rebeca Vitoria Salazar", "github": "rebecavitoriasalazar-cpu"},
]

PITCH_CARDS = [
    {
        "label": "Problema",
        "body": (
            "Catalogos com centenas de milhares de faixas, mas a experiencia "
            "de descoberta continua sendo ranking e playlist generica — sem "
            "dialogo, sem explicacao do porque da recomendacao."
        ),
    },
    {
        "label": "Timing de mercado",
        "body": (
            "Mercado global de streaming ainda em expansao (+6,4% a/a) — e o "
            "Brasil subiu 3 posicoes no ranking IFPI em 2 anos, crescendo "
            "14,1% em 2025: momentum superior a media global, no mercado de "
            "origem do time."
        ),
    },
    {
        "label": "Concorrencia",
        "body": (
            "HHI ≈ 2377 e concentracao moderada, nao monopolio: Spotify "
            "lidera com 31,4%, mas quase 70% do mercado esta dividido ou em "
            "plataformas que nao abrem seu motor de recomendacao a auditoria."
        ),
    },
    {
        "label": "A solucao — em desenho",
        "body": (
            "O desenho tecnico exato de como o agente vai funcionar ainda "
            "esta sendo consolidado pelo time. Os principios ja definidos: a "
            "recomendacao sempre parte de uma faixa que existe de verdade no "
            "catalogo (nunca uma faixa inventada), e a experiencia precisa "
            "continuar funcionando mesmo se algum servico externo falhar no "
            "meio de uma demonstracao."
        ),
    },
]

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
    {
        "id": "mercado",
        "title": "Mercado de Streaming",
        "description": "Panorama do mercado global e do Brasil, e o pitch de investimento do agente. Analise em Julia.",
        "href": "mercado.html",
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


def load_dataset_profile(profile_path: Path) -> dict:
    """Parse dataset_profile.json once; shared by the home tiles and the overview page."""
    with open(profile_path, encoding="utf-8") as f:
        return json.load(f)


def load_home_tiles(profile_path: Path) -> list[dict]:
    """Headline stats for the landing page: dataset size + curated market numbers."""
    profile = load_dataset_profile(profile_path)
    return [
        {"label": "Faixas analisadas", "value": f"{profile['total_tracks']:,}".replace(",", ".")},
        {"label": "Generos", "value": str(profile["unique_genres"])},
        {"label": "Crescimento Brasil (2025)", "value": "+14,1%", "sub": "vs +6,4% global"},
        {"label": "Mercado global 2025", "value": "US$ 31,7bi", "sub": "IFPI 2026"},
    ]


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


def load_table_rows(csv_path: Path, columns: list[str]) -> list[list]:
    """Read a CSV into the row-of-lists shape analise.html's table block needs."""
    df = pd.read_csv(csv_path)
    return df[columns].values.tolist()


def load_market_share_rows(csv_path: Path) -> list[list]:
    """Format platform_market_share.csv rows, flagging estimated/derived values."""
    df = pd.read_csv(csv_path)
    rows = []
    for _, row in df.iterrows():
        subs = "-" if pd.isna(row["subscribers_estimate_millions"]) else f"{row['subscribers_estimate_millions']:g}"
        rows.append(
            [
                row["platform"],
                f"{row['share_pct']:.1f}%",
                subs,
                row["disclosure_type"],
            ]
        )
    return rows


def build() -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)

    index_html = env.get_template("index.html").render(
        title="Analises",
        analyses=ANALYSES,
        team=TEAM,
        tiles=load_home_tiles(PROFILE_JSON),
        pitch=PITCH_CARDS,
    )
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

    total_tracks_display = f"{load_dataset_profile(PROFILE_JSON)['total_tracks']:,}".replace(",", ".")

    visao_geral_html = env.get_template("analise.html").render(
        title="Visao Geral do Dataset",
        eyebrow="Dataset Spotify · visao geral",
        heading="Visao Geral do Dataset",
        description=(
            f"{total_tracks_display} linhas no dataset bruto, mas nem toda linha "
            "e uma faixa distinta: a mesma musica pode aparecer sob mais de um "
            "genero. Numeros calculados diretamente de dataset.csv."
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
            "rows": [
                [col_a, col_b, f"{correlation:.3f}"]
                for col_a, col_b, correlation in load_table_rows(
                    CORRELATIONS_CSV, ["column_a", "column_b", "correlation"]
                )
            ],
        },
    )
    (DIST_DIR / "correlacoes.html").write_text(correlacoes_html, encoding="utf-8")

    mercado_html = env.get_template("analise.html").render(
        title="Mercado de Streaming",
        eyebrow="Analise de mercado · gerada em Julia (CSV.jl, DataFrames.jl, Plots.jl)",
        heading="Mercado de Streaming de Musica",
        description=(
            "Panorama do mercado global e do Brasil, mais o pitch de investimento "
            "do agente de recomendacao, a partir de dados curados de Spotify, "
            "IFPI, Pro-Musica Brasil e MIDiA Research (agosto/2026). Numeros "
            "calculados por nos ou vindos de estimativas de terceiros estao "
            "marcados como tal no relatorio completo: analise_mercado_streaming/"
            "RELATORIO.md (proveniencia detalhada em data/FONTES.md)."
        ),
        download={"href": MARKET_REPORT_PDF.name, "label": "Baixar relatorio em PDF"},
        tiles=[
            {"label": "MAU Spotify (7 trimestres)", "value": "+15,1%", "sub": "675M -> 777M, oficial"},
            {"label": "Premium Spotify (7 trimestres)", "value": "+14,1%", "sub": "263M -> 300M, oficial"},
            {"label": "Mercado global 2025", "value": "US$ 31,7bi", "sub": "69,6% streaming, IFPI 2026"},
            {"label": "Crescimento Brasil 2025", "value": "+14,1%", "sub": "vs +6,4% global (2,2x)"},
            {"label": "Ranking global do Brasil", "value": "#8", "sub": "#10 (2023) -> #8 (2025)"},
            {"label": "HHI plataformas", "value": "~2377", "sub": "concentracao moderada"},
        ],
        figures=[
            {"image": png.name, "alt": f"Grafico de mercado: {png.stem}", "caption": png.name}
            for png in MARKET_PNGS
        ],
        table={
            "title": "Participacao de mercado entre plataformas (fim de 2025, MIDiA Research)",
            "headers": ["Plataforma", "Participacao", "Assinantes (M)", "Divulgacao"],
            "rows": load_market_share_rows(MARKET_SHARE_CSV),
        },
    )
    (DIST_DIR / "mercado.html").write_text(mercado_html, encoding="utf-8")

    shutil.copytree(STATIC_DIR, DIST_DIR / "static")
    all_pngs = (
        GENRE_PNGS
        + [fig["path"] for analysis in STATIC_ANALYSES for fig in analysis["figures"]]
        + [ARTIST_DIST_PNG, ALBUM_DIST_PNG, CORRELATION_HEATMAP_PNG]
        + MARKET_PNGS
    )
    for png in all_pngs:
        shutil.copy(png, DIST_DIR / png.name)
    shutil.copy(MARKET_REPORT_PDF, DIST_DIR / MARKET_REPORT_PDF.name)

    print(f"Site gerado em {DIST_DIR}")


if __name__ == "__main__":
    build()
