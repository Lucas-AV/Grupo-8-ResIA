"""Perfil mínimo e auditável do usuário."""

from pydantic import BaseModel, ConfigDict, Field


class PerfilUsuario(BaseModel):
    """Sinais resumidos; não contém token OAuth nem histórico bruto."""

    model_config = ConfigDict(extra="forbid")

    id_pseudonimo: str | None = None
    artistas_preferidos: list[str] = Field(default_factory=list)
    generos_preferidos: list[str] = Field(default_factory=list)
    artistas_evitar: list[str] = Field(default_factory=list)
    generos_evitar: list[str] = Field(default_factory=list)
    faixas_conhecidas: list[str] = Field(default_factory=list)
    faixas_rejeitadas: list[str] = Field(default_factory=list)
    faixas_curtidas: list[str] = Field(default_factory=list)
    faixas_ja_exibidas: list[str] = Field(default_factory=list)
    contexto_atual: str | None = None
    cluster_id: int | None = None

