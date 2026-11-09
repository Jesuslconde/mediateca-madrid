from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MEDIATECA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    database_url: str = "postgresql+psycopg://mediateca:mediateca@localhost:5432/mediateca"
    meilisearch_url: str = "http://localhost:7700"
    meilisearch_key: str = "masterKey"
    meilisearch_index: str = "ediciones"

    opac_base_url: str = "https://gestiona.comunidad.madrid"
    opac_path: str = "/biblio_publicas/cgi-bin/abnetopac"

    api_cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.api_cors_origins.split(",") if item.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
