"""Nomes de configuração; nenhum segredo possui valor padrão."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracao(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://127.0.0.1:8000/auth/spotify/callback"
    spotify_modo: str = "demo"
    spotify_url_frontend: str = "http://127.0.0.1:3000"
    spotify_timeout_segundos: int = Field(default=10, ge=1, le=60)
    spotify_max_tentativas: int = Field(default=3, ge=0, le=5)
    spotify_cookie_secure: bool = False
    openai_api_key: str = ""
    limiar_confianca: float = Field(default=0.90, ge=0, le=1)
    chave_revisao_humana: str = ""
    caminho_banco_sqlite: str = "./dados/sistema/spotify_insights.db"
    ambiente: str = "desenvolvimento"
