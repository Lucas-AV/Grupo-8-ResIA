"""Builds the static GitHub Pages site into site/dist/."""

import json
import shutil
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader
from nbconvert import HTMLExporter
from pygments.formatters import HtmlFormatter

ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SITE_DIR / "templates"
STATIC_DIR = SITE_DIR / "static"
DIST_DIR = SITE_DIR / "dist"

NOTEBOOK_PATH = ROOT / "analise_exploratoria.ipynb"

GENRE_CSV = ROOT / "data" / "analytics" / "occurrences_by_genre.csv"
GENRE_PNGS = [ROOT / "images" / "genre_popularity.png", ROOT / "images" / "genre_energy_dance.png"]

PROFILE_JSON = ROOT / "data" / "analytics" / "dataset_profile.json"
MULTI_GENRE_CSV = ROOT / "data" / "analytics" / "dataset_multi_genre_tracks.csv"
ARTIST_DIST_PNG = ROOT / "images" / "artist_track_distribution.png"
ALBUM_DIST_PNG = ROOT / "images" / "album_track_distribution.png"

CORRELATIONS_CSV = ROOT / "data" / "analytics" / "correlations_top_pairs.csv"
CORRELATION_HEATMAP_PNG = ROOT / "images" / "correlation_heatmap.png"

MARKET_DIR = ROOT / "analise_mercado_streaming"
MARKET_SHARE_CSV = MARKET_DIR / "data" / "platform_market_share.csv"
MARKET_DATA_CSVS = [
    MARKET_DIR / "data" / "spotify_quarterly.csv",
    MARKET_DIR / "data" / "global_market_revenue.csv",
    MARKET_DIR / "data" / "global_paid_subscribers.csv",
    MARKET_DIR / "data" / "brazil_market.csv",
    MARKET_SHARE_CSV,
]
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

REPO_URL = "https://github.com/Lucas-AV/Grupo-8-ResIA"
# Ainda nao ha hospedagem publica do agente (Epico 8, ticket 8.7, bloqueado —
# ver agente_conversacional/README.md): o CTA "Testar o Agente" do ticket
# 12.6 linka pro passo a passo de como rodar localmente, nao pra um demo ao vivo.
AGENTE_DEMO_URL = f"{REPO_URL}/tree/main/agente_conversacional#readme"

TEAM = [
    {"name": "Lucas Alves Vilela", "github": "Lucas-AV"},
    {"name": "Dayane Ferreira", "github": "dayarierref"},
    {"name": "Eduarda Reis", "github": "dudsstar16"},
    {"name": "Ruan Sobreira Carvalho", "github": "Ruan-Carvalho"},
    {"name": "Felipe Matheus", "github": "femathrl0"},
    {"name": "Rebeca Vitoria Salazar", "github": "rebecavitoriasalazar-cpu"},
]

def build_pitch_cards(profile: dict) -> list[dict]:
    """Monta o pitch com as contagens do perfil gerado pelo pipeline."""
    registros = f"{profile['total_tracks']:,}".replace(",", ".")
    faixas_unicas = f"{profile['unique_track_ids']:,}".replace(",", ".")
    repeticoes = f"{profile['duplicate_rows']:,}".replace(",", ".")
    generos = profile["unique_genres"]
    return [
        {
            "label": "Problema",
            "body": (
                "Catalogos com milhares de faixas ainda oferecem descoberta "
                "baseada em ranking e playlist generica, sem dialogo nem uma "
                "explicacao simples para cada recomendacao."
            ),
        },
        {
            "label": "Timing de mercado",
            "body": (
                "O mercado global de streaming cresceu 6,4% em 2025. O Brasil "
                "cresceu 14,1% no mesmo ano e avancou do 10o para o 8o lugar "
                "no ranking mundial entre 2023 e 2025."
            ),
        },
        {
            "label": "Concorrencia",
            "body": (
                "O Spotify lidera com 31,4% da participacao estimada, mas quase "
                "70% do mercado esta distribuido entre outras plataformas."
            ),
        },
        {
            "label": "A solucao — arquitetura definida",
            "body": (
                "O MelodIA entende o pedido com regras e LLM, mas escolhe as "
                "faixas por uma busca controlada em Python. A resposta so pode "
                "citar musicas realmente devolvidas pelo catalogo."
            ),
        },
        {
            "label": "Por que o risco tecnico e controlavel",
            "body": (
                f"O conjunto processado tem {registros} registros, "
                f"{faixas_unicas} faixas unicas e {generos} generos. O motor "
                "usa metadados e caracteristicas de audio que ja estao locais."
            ),
        },
        {
            "label": "Vantagem etica como diferencial",
            "body": (
                "O produto mede diversidade e cobertura das respostas e audita "
                "as faixas citadas pelo texto gerado."
            ),
        },
        {
            "label": "O que o investimento habilita",
            "body": (
                "Dados reais de interacao ajudam a combinar similaridade de "
                "conteudo com preferencias observadas, mantendo o login Spotify "
                "como recurso opcional."
            ),
        },
        {
            "label": "Riscos assumidos, nao escondidos",
            "body": (
                f"{repeticoes} registros repetem um track_id porque uma faixa "
                "pode aparecer em varios generos. A busca remove a repeticao "
                "do resultado sem apagar essa informacao da analise."
            ),
        },
    ]

ANALYSES = [
    {
        "id": "genero",
        "title": "Perfil dos Generos",
        "nav": "Generos",
        "description": "Popularidade e caracteristicas de audio por genero musical.",
        "href": "genero.html",
    },
    {
        "id": "modo",
        "title": "Escala por Genero",
        "nav": "Modo",
        "description": "Proporcao de faixas em escala maior vs. menor, por genero.",
        "href": "modo.html",
    },
    {
        "id": "popularidade",
        "title": "Popularidade x Catalogo do Artista",
        "nav": "Popularidade",
        "description": "Popularidade media da faixa conforme o numero de faixas do artista na base.",
        "href": "popularidade.html",
    },
    {
        "id": "visao-geral",
        "title": "Visao Geral do Dataset",
        "nav": "Visao Geral",
        "description": "Estatisticas gerais, duplicatas e distribuicao de faixas por artista/album.",
        "href": "visao-geral.html",
    },
    {
        "id": "correlacoes",
        "title": "Correlacoes",
        "nav": "Correlacoes",
        "description": "Correlacao entre popularidade, duracao e features de audio.",
        "href": "correlacoes.html",
    },
    {
        "id": "mercado",
        "title": "Mercado de Streaming",
        "nav": "Mercado",
        "description": "Panorama do mercado global e do Brasil, e o pitch de investimento do agente. Analise em Julia.",
        "href": "mercado.html",
    },
    {
        "id": "personas",
        "title": "Personas do Agente",
        "nav": "Personas",
        "description": "Quatro perfis de usuario que ilustram os principais caminhos do pipeline conversacional (Proposta B).",
        "href": "personas.html",
    },
    {
        "id": "notebook",
        "title": "Notebook de Analise Exploratoria",
        "nav": "Notebook",
        "description": "Celulas e graficos do analise_exploratoria.ipynb, renderizados direto do repositorio.",
        "href": "notebook.html",
    },
]

PERSONAS = [
    {
        "initials": "M",
        "name": "Marina, 24",
        "role": "Ouvinte casual anonimo",
        "quote": "So quero um som pra hoje, nao quero criar conta pra isso.",
        "context": (
            "Abre o app direto do link, sem pensar em fazer cadastro. Pede "
            "coisas rapidas, tipo genero ou humor do momento."
        ),
        "goals": [
            "Descobrir musica rapido, sem atrito.",
            "Testar o produto antes de considerar criar conta ou logar com o Spotify.",
        ],
        "pains": [
            "Apps que pedem login antes de mostrar qualquer valor.",
            "Respostas genericas demais, sem levar o pedido a serio.",
        ],
        "scenario": (
            "Digita “quero pagode” e o roteador reconhece na hora, sem "
            "chamar o LLM (caso de uso 1). Mais tarde manda “tudo bem?” e "
            "recebe uma resposta de boas-vindas, sem forcar uma busca (caso "
            "de uso 9)."
        ),
        "tags": ["Roteador deterministico", "Sessao anonima"],
    },
    {
        "initials": "D",
        "name": "Diego, 31",
        "role": "Fa do Spotify que loga",
        "quote": "Quero que o app ja saiba o que eu curto, sem eu ter que explicar tudo de novo.",
        "context": (
            "Assinante Spotify Premium, ouve muito hip-hop e eletronica. "
            "Conecta a conta assim que descobre que da pra logar."
        ),
        "goals": [
            "Receber recomendacao alinhada ao historico real de escuta.",
            "Nao perder o contexto da conversa ao logar no meio dela.",
        ],
        "pains": [
            "Perfil de gosto generico que ignora o que ele realmente ouve.",
            "Ter que logar de novo toda hora por token expirado.",
        ],
        "scenario": (
            "Comeca a conversa anonimo, loga no meio (caso de uso 11) e a "
            "sessao e promovida sem perder historico. Buscas seguintes "
            "passam a usar o perfil_usuario calculado do centroide das "
            "faixas casadas (caso de uso 3)."
        ),
        "tags": ["Spotify OAuth", "Perfil de gosto"],
    },
    {
        "initials": "B",
        "name": "Bea, 27",
        "role": "Pede em linguagem livre",
        "quote": "Nao sei o nome de nenhum genero, so sei como eu quero me sentir.",
        "context": (
            "Nao pensa em musica por genero ou BPM. Descreve estado de "
            "espirito e espera que o app entenda."
        ),
        "goals": [
            "Ser entendida em linguagem natural, sem aprender termos tecnicos.",
            "Refinar o pedido em cima da resposta anterior sem repetir tudo de novo.",
        ],
        "pains": [
            "Apps que so aceitam filtro tecnico (genero, BPM, energia numerica).",
            "Perder o contexto da conversa a cada nova mensagem.",
        ],
        "scenario": (
            "Manda “algo pra relaxar depois de um dia puxado”, o roteador "
            "nao reconhece e a extracao via LLM entra em acao (caso de uso "
            "2). Depois manda “gostei, mas algo menos agitado” e a "
            "extracao usa o historico da sessao pra entender o refinamento "
            "(caso de uso 5)."
        ),
        "tags": ["Extracao via LLM", "Refinamento multi-turno"],
    },
    {
        "initials": "R",
        "name": "Rene, 45",
        "role": "Cauteloso com privacidade e conteudo",
        "quote": "Antes de eu clicar em “Conectar com Spotify”, me diz exatamente o que voces vao ler da minha conta.",
        "context": (
            "Usa o app com a familia por perto, evita conteudo explicito "
            "tocando em casa. Desconfia de app que pede acesso a conta sem "
            "explicar por que."
        ),
        "goals": [
            "Entender exatamente quais dados sao lidos e pra que antes de logar.",
            "Filtrar conteudo explicito das recomendacoes.",
        ],
        "pains": [
            "Tela de permissao vaga, sem dizer o que e lido.",
            "Apps que nao dizem o que fazem com o historico de escuta depois do login.",
        ],
        "scenario": (
            "Le o aviso de consentimento antes do OAuth, que lista os 3 "
            "scopes read-only pedidos e confirma que nada alem dos tokens "
            "fica persistido (ticket 5.10). Ativa excluir_explicit=true e "
            "confere que a resposta nunca cita faixa explicita (caso de uso "
            "7)."
        ),
        "tags": ["Aviso de consentimento", "excluir_explicit"],
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
        "tiles": [
            {"label": "Escala maior (geral)", "value": "63,5%", "sub": "media de todos os generos", "icon": "pie-chart"},
            {"label": "Genero mais em escala maior", "value": "Country", "sub": "88,9% das faixas", "icon": "trending-up"},
            {"label": "Genero mais em escala menor", "value": "Deep-house", "sub": "53,8% das faixas em escala menor", "icon": "trending-down"},
        ],
        "figures": [
            {
                "path": ROOT / "images" / "genre_mode.png",
                "alt": "Grafico de barras empilhadas: proporcao de escala maior e menor por genero",
                "caption": "Escala maior vs. menor por genero",
                "leitura": (
                    "Em media, 63,5% das faixas do dataset estao em escala maior — "
                    "mas isso varia bastante por genero. Country e o extremo de "
                    "escala maior (88,9% das faixas), coerente com a tradicao "
                    "harmonica do genero. Deep-house e o unico genero onde a "
                    "escala menor predomina (53,8% das faixas), o que combina com "
                    "o tom mais introspectivo e atmosferico tipico do estilo. Nao "
                    "ha correlacao obvia entre escala e popularidade — e mais um "
                    "reflexo de convencao estilistica de cada genero do que um "
                    "sinal comercial."
                ),
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
        "tiles": [
            {"label": "Artistas com 1 faixa", "value": "6.148", "sub": "56,5% da base de artistas", "icon": "users"},
            {"label": "Popularidade media (1 faixa)", "value": "35,7", "sub": "vs 26,6 em artistas com 21+ faixas", "icon": "trending-down"},
            {"label": "Artista com mais faixas", "value": "171", "sub": "my little airport, no dataset", "icon": "trophy"},
        ],
        "figures": [
            {
                "path": ROOT / "images" / "popularity_occurrences.png",
                "alt": "Grafico de barras: popularidade media por faixa de quantidade de ocorrencias do artista",
                "caption": "Popularidade media por faixa de ocorrencias do artista",
                "leitura": (
                    "A tendencia e inversa ao que se poderia esperar: quanto mais "
                    "faixas um artista tem na base, menor a popularidade media "
                    "delas — de 35,7 pontos para artistas com so 1 faixa ate 26,6 "
                    "pontos para os com 21+ faixas. Mais da metade dos artistas "
                    "(6.148 de 10.872, 56,5%) aparece so uma vez na base. Uma "
                    "leitura possivel: artistas com catalogo grande tendem a ter "
                    "faixas mais nichadas/antigas diluindo a media, enquanto "
                    "quem aparece uma unica vez tende a ser um single de maior "
                    "impacto recente. Nao e evidencia de causalidade — so uma "
                    "correlacao a se ter em mente ao usar contagem de faixas "
                    "como sinal de relevancia do artista."
                ),
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
        {"label": "Registros analisados", "value": f"{profile['total_tracks']:,}".replace(",", "."), "icon": "music"},
        {"label": "Generos", "value": str(profile["unique_genres"]), "icon": "layers"},
        {"label": "Crescimento Brasil (2025)", "value": "+14,1%", "sub": "vs +6,4% global", "icon": "trending-up"},
        {"label": "Mercado global 2025", "value": "US$ 31,7bi", "sub": "IFPI 2026", "icon": "globe"},
    ]


def load_profile_tiles(profile_path: Path) -> list[dict]:
    """Turn dataset_profile.json into the tile list visao-geral.html renders."""
    profile = load_dataset_profile(profile_path)
    total_nulls = sum(profile["null_counts"].values())
    return [
        {"label": "Registros na base", "value": f"{profile['total_tracks']:,}".replace(",", "."), "icon": "music"},
        {
            "label": "Faixas unicas",
            "value": f"{profile['unique_track_ids']:,}".replace(",", "."),
            "sub": f"{profile['duplicate_rows']} linhas duplicadas (mesma faixa em outro genero)",
            "icon": "check-badge",
        },
        {"label": "Artistas", "value": f"{profile['unique_artists']:,}".replace(",", "."), "icon": "users"},
        {"label": "Albuns", "value": f"{profile['unique_albums']:,}".replace(",", "."), "icon": "disc"},
        {"label": "Generos", "value": str(profile["unique_genres"]), "icon": "layers"},
        {"label": "Valores nulos", "value": str(total_nulls), "icon": "alert"},
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


def render_notebook_html(notebook_path: Path) -> tuple[str, str]:
    """Convert the notebook to an embeddable HTML fragment + its pygments CSS."""
    exporter = HTMLExporter(template_name="basic")
    body, _resources = exporter.from_filename(str(notebook_path))
    pygments_css = HtmlFormatter().get_style_defs(".notebook-embed .highlight")
    return body, pygments_css


def build() -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)

    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)
    env.globals["nav_items"] = ANALYSES
    profile = load_dataset_profile(PROFILE_JSON)
    pitch_cards = build_pitch_cards(profile)
    total_tracks = f"{profile['total_tracks']:,}".replace(",", ".")
    unique_tracks = f"{profile['unique_track_ids']:,}".replace(",", ".")

    index_html = env.get_template("index.html").render(
        title="Analises",
        current_page="index.html",
        analyses=ANALYSES,
        team=TEAM,
        tiles=load_home_tiles(PROFILE_JSON),
        pitch=pitch_cards,
        hero_records=total_tracks,
        hero_unique=unique_tracks,
        hero_genres=profile["unique_genres"],
    )
    (DIST_DIR / "index.html").write_text(index_html, encoding="utf-8")

    pitch_by_label = {card["label"]: card for card in pitch_cards}
    landing_html = env.get_template("landing.html").render(
        title="Landing",
        current_page="landing.html",
        pitch=pitch_cards,
        problema=pitch_by_label["Problema"],
        solucao=pitch_by_label["A solucao — arquitetura definida"],
        tiles=load_home_tiles(PROFILE_JSON),
        repo_url=REPO_URL,
        agente_url=AGENTE_DEMO_URL,
        unique_tracks=unique_tracks,
        hero_genres=profile["unique_genres"],
    )
    (DIST_DIR / "landing.html").write_text(landing_html, encoding="utf-8")

    rows = load_genre_rows(GENRE_CSV)
    genero_html = env.get_template("genero.html").render(
        title="Perfil dos Generos",
        current_page="genero.html",
        rows_json=rows_to_embeddable_json(rows),
    )
    (DIST_DIR / "genero.html").write_text(genero_html, encoding="utf-8")

    for analysis in STATIC_ANALYSES:
        html = env.get_template("analise.html").render(
            title=analysis["heading"],
            current_page=analysis["href"],
            eyebrow=analysis["eyebrow"],
            heading=analysis["heading"],
            description=analysis["description"],
            tiles=analysis.get("tiles"),
            figures=[
                {
                    "image": fig["path"].name,
                    "alt": fig["alt"],
                    "caption": fig.get("caption", fig["path"].name),
                    "leitura": fig.get("leitura"),
                }
                for fig in analysis["figures"]
            ],
        )
        (DIST_DIR / analysis["href"]).write_text(html, encoding="utf-8")

    total_tracks_display = total_tracks

    visao_geral_html = env.get_template("analise.html").render(
        title="Visao Geral do Dataset",
        current_page="visao-geral.html",
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
                "caption": "Artistas por faixa de numero de musicas na base",
                "leitura": (
                    "A base e dominada por artistas com pouquissimas faixas: "
                    "6.148 dos 10.872 artistas (56,5%) aparecem so uma vez, e "
                    "2.121 (19,5%) aparecem exatamente duas vezes — juntos, esses "
                    "dois grupos ja somam 76% de todos os artistas. So 181 "
                    "artistas (1,7%) tem 21 ou mais faixas na base. E uma "
                    "distribuicao de cauda longa tipica de catalogos musicais: "
                    "poucos artistas com catalogo extenso, muitos com presenca "
                    "pontual."
                ),
            },
            {
                "image": ALBUM_DIST_PNG.name,
                "alt": "Grafico de barras: quantidade de albuns por faixa de numero de musicas na base",
                "caption": "Albuns por faixa de numero de musicas na base",
                "leitura": (
                    "O padrao se repete com albuns, ainda mais concentrado: "
                    "10.351 dos 15.481 albuns (66,9%) tem apenas uma faixa "
                    "presente na base — provavelmente singles ou faixas isoladas "
                    "amostradas de albuns maiores, nao o album completo. Apenas "
                    "91 albuns (0,6%) tem 21 ou mais faixas amostradas. Isso "
                    "reforca que o dataset e uma amostra por faixa/genero, nao "
                    "uma colecao de albuns completos."
                ),
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
        current_page="correlacoes.html",
        eyebrow="Dataset Spotify · correlacao entre variaveis numericas",
        heading="Correlacoes entre popularidade, duracao e audio",
        description=(
            "Correlacao de Pearson entre popularidade, duracao e as 9 features "
            "de audio continuas do dataset (key, mode e time_signature ficam "
            "de fora por nao serem continuas)."
        ),
        tiles=[
            {"label": "Correlacao mais forte", "value": "0,775", "sub": "energia x loudness", "icon": "trending-up"},
            {"label": "Correlacao negativa mais forte", "value": "-0,742", "sub": "energia x acousticness", "icon": "trending-down"},
            {"label": "Pares analisados", "value": "36", "sub": "combinacoes de 9 features continuas", "icon": "pie-chart"},
        ],
        figures=[
            {
                "image": CORRELATION_HEATMAP_PNG.name,
                "alt": "Heatmap de correlacao entre popularidade, duracao e features de audio",
                "caption": "Heatmap de correlacao de Pearson",
                "leitura": (
                    "As correlacoes mais fortes do dataset sao intuitivas: energia "
                    "e loudness andam quase juntas (r=0,775 — faixas mais altas "
                    "tendem a soar mais energeticas), e energia e acousticness "
                    "sao quase opostas (r=-0,742 — faixas acusticas tendem a ser "
                    "menos energeticas, e vice-versa). Danceability e valence "
                    "tambem se correlacionam de forma moderada (r=0,512): faixas "
                    "mais dancantes tendem a soar mais positivas/alegres. "
                    "Nenhuma feature isolada explica popularidade sozinha — a "
                    "correlacao mais forte com popularity nesta tabela nem "
                    "aparece no top 10, sinal de que popularidade depende mais "
                    "de fatores fora do audio (artista, marketing, timing) do "
                    "que das caracteristicas sonoras da faixa."
                ),
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
        current_page="mercado.html",
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
        pitch=pitch_cards,
        tiles=[
            {"label": "MAU Spotify (7 trimestres)", "value": "+15,1%", "sub": "675M -> 777M, oficial", "icon": "users"},
            {"label": "Premium Spotify (7 trimestres)", "value": "+14,1%", "sub": "263M -> 300M, oficial", "icon": "star"},
            {"label": "Mercado global 2025", "value": "US$ 31,7bi", "sub": "69,6% streaming, IFPI 2026", "icon": "globe"},
            {"label": "Crescimento Brasil 2025", "value": "+14,1%", "sub": "vs +6,4% global (2,2x)", "icon": "trending-up"},
            {"label": "Ranking global do Brasil", "value": "#8", "sub": "#10 (2023) -> #8 (2025)", "icon": "trophy"},
            {"label": "HHI plataformas", "value": "~2377", "sub": "concentracao moderada", "icon": "pie-chart"},
        ],
        figures=[
            {
                "image": "output_spotify_usuarios.png",
                "alt": "Grafico de linhas: MAU e assinantes Premium do Spotify por trimestre",
                "caption": "MAU e assinantes Premium por trimestre",
                "leitura": (
                    "As duas linhas sobem juntas e quase no mesmo ritmo: MAU passou "
                    "de 675M para 777M (+15,1%) enquanto assinantes Premium foram de "
                    "263M para 300M (+14,1%) nos mesmos 7 trimestres. O Spotify nao "
                    "esta so atraindo mais gente de graca — esta convertendo essas "
                    "pessoas em assinante pagante numa proporcao quase identica ao "
                    "crescimento da base total. Bom sinal de saude do negocio: a taxa "
                    "de conversao de usuario gratis pra pago nao esta caindo conforme "
                    "a base cresce."
                ),
                "csv": "spotify_quarterly.csv",
                "table": {
                    "title": "MAU e Premium por trimestre",
                    "headers": ["Trimestre", "MAU (M)", "Premium (M)"],
                    "rows": [
                        ["2024-Q4", 675, 263],
                        ["2025-Q1", 678, 268],
                        ["2025-Q2", 696, 276],
                        ["2025-Q3", 713, 281],
                        ["2025-Q4", 751, 290],
                        ["2026-Q1", 761, 293],
                        ["2026-Q2", 777, 300],
                    ],
                },
            },
            {
                "image": "output_spotify_receita.png",
                "alt": "Grafico de linhas: receita total do Spotify por trimestre",
                "caption": "Receita total por trimestre",
                "leitura": (
                    "A receita sobe de forma quase constante trimestre a trimestre, "
                    "de €4.242M (2024-Q4) ate €4.777M (2026-Q2) — sem quedas bruscas "
                    "no meio do caminho. Tipico de negocio de assinatura: a receita "
                    "ja “contratada” (assinantes que pagam todo mes, "
                    "independente de quanto usam o app naquele mes) segura o "
                    "resultado mesmo em trimestres sazonalmente mais fracos, "
                    "diferente de um negocio que depende de compras pontuais."
                ),
                "csv": "spotify_quarterly.csv",
                "table": {
                    "title": "Receita total por trimestre",
                    "headers": ["Trimestre", "Receita total (EUR M)"],
                    "rows": [
                        ["2024-Q4", 4242],
                        ["2025-Q1", 4190],
                        ["2025-Q2", 4193],
                        ["2025-Q3", 4272],
                        ["2025-Q4", 4531],
                        ["2026-Q1", 4533],
                        ["2026-Q2", 4777],
                    ],
                },
            },
            {
                "image": "output_spotify_margem.png",
                "alt": "Grafico de linhas: margem operacional do Spotify por trimestre",
                "caption": "Margem operacional por trimestre",
                "leitura": (
                    "Margem operacional e quanto sobra de lucro depois das despesas "
                    "do negocio, pra cada real que entra — e ela varia bem mais que "
                    "receita ou usuarios: de um minimo de 9,7% ate um pico de 15,8% "
                    "no periodo observado. Normal: pequenas mudancas em custo de "
                    "licenciamento de musica ou em campanhas de marketing pontuais "
                    "pesam proporcionalmente mais numa fatia fina (margem) do que em "
                    "numeros grandes e mais estaveis (usuarios, receita)."
                ),
                "csv": "spotify_quarterly.csv",
                "table": {
                    "title": "Margem operacional por trimestre",
                    "headers": ["Trimestre", "Margem operacional (%)"],
                    "rows": [
                        ["2024-Q4", "11,2%"],
                        ["2025-Q1", "12,1%"],
                        ["2025-Q2", "9,7%"],
                        ["2025-Q3", "13,6%"],
                        ["2025-Q4", "15,5%"],
                        ["2026-Q1", "15,8%"],
                        ["2026-Q2", "—"],
                    ],
                },
            },
            {
                "image": "output_mercado_global.png",
                "alt": "Grafico de barras: receita global de musica gravada, total vs. streaming",
                "caption": "Receita global de musica gravada, total vs. streaming",
                "leitura": (
                    "A fatia de streaming (US$ 22,06bi) ja e bem maior que o resto do "
                    "mercado de musica gravada somado (CD, vinil, downloads, direitos "
                    "de radio/TV etc.) dentro do total de US$ 31,7bi em 2025. "
                    "Streaming deixou de ser “um jeito a mais” de ouvir "
                    "musica e virou o motor principal da industria inteira — o "
                    "mercado global cresceu 6,4% em 2025, acelerando frente aos 4,7% "
                    "de 2024."
                ),
                "csv": "global_market_revenue.csv",
                "table": {
                    "title": "Receita global de musica gravada",
                    "headers": ["Ano", "Receita total (US$ bi)", "Receita streaming (US$ bi)"],
                    "rows": [
                        [2014, 13.1, "—"],
                        [2024, 29.6, 20.4],
                        [2025, 31.7, 22.06],
                    ],
                },
            },
            {
                "image": "output_assinantes_globais.png",
                "alt": "Grafico de barras: crescimento de assinantes pagos de streaming no mundo",
                "caption": "Crescimento de assinantes pagos no mundo",
                "leitura": (
                    "A linha continua subindo — de 509 milhoes em 2021 para 837 "
                    "milhoes em 2025 — mas os degraus entre um ano e outro estao "
                    "ficando menores: 94 milhoes de novos assinantes liquidos em "
                    "2022 cairam para 73 milhoes em 2025. O mercado esta "
                    "amadurecendo. Isso muda a estrategia: crescer so “roubando” "
                    "gente que ainda nao assina nenhum servico fica mais dificil a "
                    "cada ano; fazer quem ja assina usar mais e cancelar menos vira "
                    "o jogo principal."
                ),
                "csv": "global_paid_subscribers.csv",
                "table": {
                    "title": "Assinantes pagos globais",
                    "headers": ["Ano", "Assinantes (M)", "Novos assinantes liq. (M)"],
                    "rows": [
                        [2021, 509, "—"],
                        [2022, 603, 94],
                        [2023, 680, 77],
                        [2024, 764, 84],
                        [2025, 837, 73],
                    ],
                },
            },
            {
                "image": "output_brasil_vs_global.png",
                "alt": "Grafico de barras: comparacao de crescimento do mercado fonografico, Brasil vs. global",
                "caption": "Crescimento do mercado fonografico — Brasil vs. global (2025)",
                "leitura": (
                    "A barra do Brasil (+14,1% em 2025) e mais que o dobro da barra "
                    "do mundo (+6,4%) — uma diferenca de 2,2 vezes. Pra quem esta "
                    "construindo um produto pensando no publico brasileiro, isso e "
                    "um bom sinal de timing: o mercado local nao esta so "
                    "“acompanhando” a tendencia global, esta crescendo mais "
                    "rapido que ela, e isso ja se reflete no ranking IFPI, onde o "
                    "Brasil subiu de #10 (2023) para #8 (2025) em dois anos."
                ),
                "csv": "brazil_market.csv",
                "table": {
                    "title": "Brasil vs. mercado global — crescimento 2025",
                    "headers": ["Mercado", "Crescimento 2025 (% a/a)"],
                    "rows": [
                        ["Brasil", "14,1%"],
                        ["Global", "6,4%"],
                    ],
                },
            },
            {
                "image": "output_market_share.png",
                "alt": "Grafico de barras: participacao de mercado entre plataformas de streaming",
                "caption": "Participacao de mercado entre plataformas",
                "leitura": (
                    "O Spotify lidera com 31,4% de participacao (300M assinantes), "
                    "mas esta longe da maioria: some Tencent Music (13,8%, 127,4M — "
                    "oficial na China), Apple Music (12,6%, estimativa de "
                    "terceiros), YouTube Music (12,4%, 125M oficial) e “Outros” "
                    "(29,8%, residuo calculado que agrega Amazon Music, Deezer, "
                    "Tidal etc.) e da quase 70% do mercado dividido. O HHI ≈ 2377 "
                    "confirma: e uma concentracao moderada, mais perto do limite "
                    "alto, nao um monopolio — ha espaco real pra um produto novo "
                    "entrar."
                ),
                "csv": "platform_market_share.csv",
                "table": {
                    "title": "Participacao de mercado entre plataformas",
                    "headers": ["Plataforma", "Participacao", "Assinantes (M)", "Divulgacao"],
                    "rows": load_market_share_rows(MARKET_SHARE_CSV),
                },
            },
        ],
        table={
            "title": "Participacao de mercado entre plataformas (fim de 2025, MIDiA Research)",
            "headers": ["Plataforma", "Participacao", "Assinantes (M)", "Divulgacao"],
            "rows": load_market_share_rows(MARKET_SHARE_CSV),
        },
    )
    (DIST_DIR / "mercado.html").write_text(mercado_html, encoding="utf-8")

    personas_html = env.get_template("personas.html").render(
        title="Personas do Agente",
        current_page="personas.html",
        eyebrow="Proposta B · pipeline conversacional",
        heading="Personas do Agente",
        description=(
            "Quatro perfis de usuario que ilustram os principais caminhos do "
            "pipeline conversacional documentado em PIPELINE_AGENTE_PROPOSTA_B.md "
            "— cada um mapeado aos casos de uso e tickets do backlog que o "
            "cobrem."
        ),
        personas=PERSONAS,
    )
    (DIST_DIR / "personas.html").write_text(personas_html, encoding="utf-8")

    notebook_body, pygments_css = render_notebook_html(NOTEBOOK_PATH)
    notebook_html = env.get_template("notebook.html").render(
        title="Notebook de Analise Exploratoria",
        current_page="notebook.html",
        eyebrow="Dataset Spotify · analise_exploratoria.ipynb",
        heading="Notebook de Analise Exploratoria",
        description=(
            "Celulas de codigo e graficos do notebook guiado que fundamenta as "
            "analises deste site, renderizados diretamente do repositorio."
        ),
        repo_href=f"{REPO_URL}/blob/main/{NOTEBOOK_PATH.name}",
        notebook_body=notebook_body,
        pygments_css=pygments_css,
    )
    (DIST_DIR / "notebook.html").write_text(notebook_html, encoding="utf-8")

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
    for csv_path in MARKET_DATA_CSVS:
        shutil.copy(csv_path, DIST_DIR / csv_path.name)

    print(f"Site gerado em {DIST_DIR}")


if __name__ == "__main__":
    build()
