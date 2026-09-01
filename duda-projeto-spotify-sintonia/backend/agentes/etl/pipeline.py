"""ETL reproduzível do Spotify Tracks Dataset para o catálogo do projeto.

O notebook acadêmico usa estas funções para que a análise e o backend adotem
as mesmas regras de limpeza, padronização e normalização.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from backend.utilitarios.normalizacao import normalizar_genero

COLUNAS_OBRIGATORIAS = {
    "track_id",
    "artists",
    "album_name",
    "track_name",
    "popularity",
    "duration_ms",
    "explicit",
    "danceability",
    "energy",
    "key",
    "loudness",
    "mode",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "time_signature",
    "track_genre",
}

ATRIBUTOS_AUDIO = [
    "danceability",
    "energy",
    "valence",
    "tempo",
    "acousticness",
    "instrumentalness",
    "speechiness",
    "liveness",
    "loudness",
]

COLUNAS_NUMERICAS = [
    "popularity",
    "duration_ms",
    "danceability",
    "energy",
    "key",
    "loudness",
    "mode",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "time_signature",
]

COLUNAS_0_A_1 = {
    "danceability",
    "energy",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
}

# A lista é intencionalmente pequena: corrige aliases inequívocos sem colapsar
# subgêneros, que são importantes para a análise acadêmica.
ALIASES_GENERO = {
    "alt rock": "alternative rock",
    "alternative rock": "alternative rock",
    "electro": "electronic",
    "edm": "electronic dance music",
    "electronic dance music": "electronic dance music",
    "hip hop": "hip hop",
    "r n b": "r&b",
    "r and b": "r&b",
    "rock n roll": "rock and roll",
    "synth pop": "synthpop",
}


@dataclass
class ResultadoETL:
    """Artefatos produzidos por uma execução do ETL."""

    dados_tratados: pd.DataFrame
    agregacao_por_genero: pd.DataFrame
    relatorio: dict[str, Any]
    normalizador: MinMaxScaler
    arquivos: dict[str, Path] = field(default_factory=dict)


def localizar_csv_bruto(diretorio: str | Path = "dados/brutos") -> Path:
    """Encontra ``dataset.csv`` ou o único CSV disponível no diretório."""

    pasta = Path(diretorio)
    padrao = pasta / "dataset.csv"
    if padrao.exists():
        return padrao

    candidatos = sorted(pasta.glob("*.csv"))
    if len(candidatos) == 1:
        return candidatos[0]
    if not candidatos:
        raise FileNotFoundError(f"Nenhum CSV encontrado em {pasta.resolve()}.")
    raise ValueError(
        "Há mais de um CSV bruto. Informe o caminho explicitamente para evitar "
        f"ambiguidade: {[arquivo.name for arquivo in candidatos]}"
    )


def hash_arquivo(caminho: str | Path) -> str:
    """Calcula SHA-256 sem carregar o arquivo inteiro em memória."""

    digest = sha256()
    with Path(caminho).open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def carregar_dataset(caminho_csv: str | Path) -> pd.DataFrame:
    """Lê e valida o schema mínimo do CSV oficial."""

    dados = pd.read_csv(caminho_csv)
    faltantes = sorted(COLUNAS_OBRIGATORIAS - set(dados.columns))
    if faltantes:
        raise ValueError(
            "O CSV não possui as colunas obrigatórias do Spotify Tracks Dataset: "
            f"{faltantes}"
        )
    return dados


def diagnosticar_dados(dados: pd.DataFrame) -> dict[str, Any]:
    """Gera o relatório inicial, sem modificar o DataFrame recebido."""

    colunas_sem_indice = [
        coluna for coluna in dados.columns if not coluna.lower().startswith("unnamed:")
    ]
    sem_indice = dados.loc[:, colunas_sem_indice]
    nulos = dados.isna().sum()
    return {
        "linhas": int(dados.shape[0]),
        "colunas": int(dados.shape[1]),
        "nomes_colunas": dados.columns.tolist(),
        "tipos": {coluna: str(tipo) for coluna, tipo in dados.dtypes.items()},
        "nulos_por_coluna": {
            coluna: int(quantidade)
            for coluna, quantidade in nulos.items()
            if quantidade > 0
        },
        "duplicatas_exatas": int(dados.duplicated().sum()),
        "duplicatas_exatas_sem_coluna_indice": int(sem_indice.duplicated().sum()),
        "track_ids_repetidos": int(sem_indice["track_id"].duplicated().sum()),
        "generos_distintos": int(sem_indice["track_genre"].nunique(dropna=True)),
    }


def padronizar_nome_genero(valor: Any) -> str:
    """Aplica limpeza textual e aliases conservadores de gênero."""

    if not isinstance(valor, str) or not valor.strip():
        return "desconhecido"
    normalizado = normalizar_genero(valor)
    return ALIASES_GENERO.get(normalizado, normalizado)


def _converter_explicit(valor: Any) -> bool | float:
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        texto = valor.strip().lower()
        if texto in {"true", "1", "sim"}:
            return True
        if texto in {"false", "0", "nao", "não"}:
            return False
    if pd.isna(valor):
        return np.nan
    return bool(valor)


def _mediana_por_genero(dados: pd.DataFrame, coluna: str) -> pd.Series:
    por_genero = dados.groupby("track_genre")[coluna].transform("median")
    return dados[coluna].fillna(por_genero).fillna(dados[coluna].median())


def _moda_ou_primeiro(valores: pd.Series) -> Any:
    validos = valores.dropna()
    if validos.empty:
        return np.nan
    moda = validos.mode()
    return moda.iloc[0] if not moda.empty else validos.iloc[0]


def _consolidar_track_ids(dados: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Mantém uma faixa por ID e registra conflitos numéricos resolvidos."""

    # A primeira ocorrência preserva metadados textuais. Os atributos numéricos
    # são agregados pela mediana, de modo que pequenas divergências não gerem
    # catálogos duplicados nem valores arbitrários.
    resultado = dados.drop_duplicates("track_id", keep="first").set_index("track_id")
    agrupado = dados.groupby("track_id", sort=False)
    resultado[COLUNAS_NUMERICAS] = agrupado[COLUNAS_NUMERICAS].median()
    resultado["explicit"] = agrupado["explicit"].first().astype(bool)

    generos = agrupado["track_genre"].agg(
        lambda valores: " | ".join(sorted(set(valores.dropna().astype(str))))
        or "desconhecido"
    )
    resultado["generos"] = generos
    resultado["track_genre"] = generos.str.split(" | ", regex=False).str[0]

    conflitos = agrupado[COLUNAS_NUMERICAS].nunique(dropna=True).gt(1)
    conflitos_numericos = int(conflitos.sum().sum())
    return resultado.reset_index(), conflitos_numericos


def tratar_dataset(dados: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Limpa, imputa e consolida o catálogo sem aplicar o scaler."""

    trabalho = dados.copy()
    colunas_indice = [
        coluna for coluna in trabalho.columns if coluna.lower().startswith("unnamed:")
    ]
    trabalho = trabalho.drop(columns=colunas_indice)

    antes = len(trabalho)
    trabalho = trabalho.drop_duplicates().copy()
    duplicatas_removidas = antes - len(trabalho)

    for coluna in COLUNAS_NUMERICAS:
        trabalho[coluna] = pd.to_numeric(trabalho[coluna], errors="coerce")
    trabalho["explicit"] = trabalho["explicit"].map(_converter_explicit)
    trabalho["track_genre"] = trabalho["track_genre"].map(padronizar_nome_genero)

    for coluna in COLUNAS_0_A_1:
        invalidos = ~trabalho[coluna].between(0, 1)
        trabalho.loc[invalidos, coluna] = np.nan
    trabalho.loc[trabalho["popularity"].lt(0) | trabalho["popularity"].gt(100), "popularity"] = np.nan
    trabalho.loc[trabalho["tempo"].le(0), "tempo"] = np.nan
    trabalho.loc[trabalho["duration_ms"].le(0), "duration_ms"] = np.nan

    faltantes_obrigatorios = trabalho[["track_id", "track_name", "artists"]].isna().any(axis=1)
    linhas_descartadas = int(faltantes_obrigatorios.sum())
    trabalho = trabalho.loc[~faltantes_obrigatorios].copy()
    trabalho["album_name"] = trabalho["album_name"].fillna("desconhecido")

    for coluna in COLUNAS_NUMERICAS:
        trabalho[coluna] = _mediana_por_genero(trabalho, coluna)
    trabalho["explicit"] = trabalho["explicit"].fillna(_moda_ou_primeiro(trabalho["explicit"]))
    trabalho["explicit"] = trabalho["explicit"].astype(bool)

    consolidado, conflitos_numericos = _consolidar_track_ids(trabalho)
    consolidado = consolidado.sort_values("track_id").reset_index(drop=True)
    relatorio = {
        "colunas_indice_removidas": colunas_indice,
        "duplicatas_exatas_removidas": duplicatas_removidas,
        "linhas_descartadas_campos_obrigatorios": linhas_descartadas,
        "faixas_consolidadas_por_track_id": int(len(trabalho) - len(consolidado)),
        "conflitos_numericos_resolvidos_por_mediana": conflitos_numericos,
        "nulos_restantes": {
            coluna: int(quantidade)
            for coluna, quantidade in consolidado.isna().sum().items()
            if quantidade > 0
        },
    }
    return consolidado, relatorio


def normalizar_atributos_audio(
    dados: pd.DataFrame, normalizador: MinMaxScaler | None = None
) -> tuple[pd.DataFrame, MinMaxScaler]:
    """Acrescenta colunas ``*_norm`` em escala 0–1 e devolve o scaler usado."""

    resultado = dados.copy()
    scaler = normalizador or MinMaxScaler()
    valores = (
        scaler.fit_transform(resultado[ATRIBUTOS_AUDIO])
        if normalizador is None
        else scaler.transform(resultado[ATRIBUTOS_AUDIO])
    )
    colunas_normalizadas = [f"{coluna}_norm" for coluna in ATRIBUTOS_AUDIO]
    resultado[colunas_normalizadas] = np.clip(valores, 0.0, 1.0)
    return resultado, scaler


def agregar_por_genero(dados_tratados: pd.DataFrame) -> pd.DataFrame:
    """Calcula contagem e médias por gênero para respostas de descoberta."""

    por_genero = dados_tratados.assign(
        genero=dados_tratados["generos"].str.split(" | ", regex=False)
    ).explode("genero")
    medias = ["popularity", *ATRIBUTOS_AUDIO, *[f"{coluna}_norm" for coluna in ATRIBUTOS_AUDIO]]
    agregacao = (
        por_genero.groupby("genero", as_index=False)
        .agg(quantidade_faixas=("track_id", "nunique"), **{f"media_{coluna}": (coluna, "mean") for coluna in medias})
        .sort_values(["quantidade_faixas", "genero"], ascending=[False, True])
        .reset_index(drop=True)
    )
    return agregacao


def _json_seguro(valor: Any) -> Any:
    if isinstance(valor, Path):
        return str(valor)
    if isinstance(valor, (np.integer, np.floating)):
        return valor.item()
    if isinstance(valor, np.ndarray):
        return valor.tolist()
    raise TypeError(f"Tipo não serializável: {type(valor)!r}")


def salvar_artefatos(
    resultado: ResultadoETL,
    diretorio_saida: str | Path = "dados/tratados",
    diretorio_modelos: str | Path = "dados/modelos",
) -> dict[str, Path]:
    """Salva catálogo, agregação, metadados e normalizador para reuso."""

    pasta_saida = Path(diretorio_saida)
    pasta_modelos = Path(diretorio_modelos)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    pasta_modelos.mkdir(parents=True, exist_ok=True)

    arquivos = {
        "catalogo_tratado": pasta_saida / "spotify_tracks_tratado.csv",
        "agregacao_generos": pasta_saida / "agregacao_por_genero.csv",
        "metadados": pasta_saida / "metadados_etl.json",
        "normalizador": pasta_modelos / "normalizador_atributos.joblib",
    }
    resultado.dados_tratados.to_csv(arquivos["catalogo_tratado"], index=False)
    resultado.agregacao_por_genero.to_csv(arquivos["agregacao_generos"], index=False)
    joblib.dump(resultado.normalizador, arquivos["normalizador"])
    with arquivos["metadados"].open("w", encoding="utf-8") as arquivo:
        json.dump(resultado.relatorio, arquivo, ensure_ascii=False, indent=2, default=_json_seguro)
    return arquivos


def executar_etl(
    caminho_csv: str | Path | None = None,
    diretorio_saida: str | Path = "dados/tratados",
    diretorio_modelos: str | Path = "dados/modelos",
    *,
    salvar: bool = True,
) -> ResultadoETL:
    """Executa o pipeline completo e, opcionalmente, persiste seus artefatos."""

    entrada = Path(caminho_csv) if caminho_csv else localizar_csv_bruto()
    dados_brutos = carregar_dataset(entrada)
    relatorio = {
        "proveniencia": {
            "arquivo": str(entrada),
            "sha256": hash_arquivo(entrada),
            "executado_em_utc": datetime.now(UTC).isoformat(),
        },
        "antes_do_tratamento": diagnosticar_dados(dados_brutos),
        "decisoes": {
            "duplicatas_exatas": "remover",
            "campos_obrigatorios": "descartar linha sem track_id, track_name ou artists",
            "nulos_numericos": "mediana por gênero; fallback para mediana global",
            "album_nulo": "preencher com desconhecido",
            "generos_repetidos": "consolidar por track_id e manter todos os gêneros",
            "normalizacao": "MinMaxScaler em colunas *_norm, preservando valores brutos",
        },
    }
    dados_limpos, relatorio_tratamento = tratar_dataset(dados_brutos)
    dados_tratados, normalizador = normalizar_atributos_audio(dados_limpos)
    agregacao = agregar_por_genero(dados_tratados)
    relatorio["tratamento"] = relatorio_tratamento
    relatorio["depois_do_tratamento"] = {
        "linhas": len(dados_tratados),
        "colunas": int(dados_tratados.shape[1]),
        "generos_distintos": int(agregacao["genero"].nunique()),
    }

    resultado = ResultadoETL(dados_tratados, agregacao, relatorio, normalizador)
    if salvar:
        resultado.arquivos = salvar_artefatos(resultado, diretorio_saida, diretorio_modelos)
    return resultado
