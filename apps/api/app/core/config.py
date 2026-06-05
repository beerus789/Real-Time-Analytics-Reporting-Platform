from functools import lru_cache
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import AnyHttpUrl, Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Pulseboard Analytics"
    environment: Literal["local", "test", "staging", "production"] = "local"
    api_v1_prefix: str = "/api/v1"
    frontend_origin: str = "http://localhost:3000"

    database_url: str = Field(
        default="postgresql+asyncpg://analytics:analytics@postgres:5432/analytics"
    )
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    access_token_secret: str = "change-me-access-secret"
    refresh_token_secret: str = "change-me-refresh-secret"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 14
    cookie_secure: bool = False
    refresh_cookie_path: str = "/"

    api_key_prefix: str = "pa"
    ingestion_rate_limit_per_minute: int = 1200
    public_share_base_url: AnyHttpUrl | None = None

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgres://"):
            value = value.replace("postgres://", "postgresql+asyncpg://", 1)
        elif value.startswith("postgresql://"):
            value = value.replace("postgresql://", "postgresql+asyncpg://", 1)
        if value.startswith("postgresql+asyncpg://"):
            value = normalize_asyncpg_ssl_params(value)
        return value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins(self) -> list[str]:
        return [self.frontend_origin]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def normalize_asyncpg_ssl_params(database_url: str) -> str:
    parsed = urlsplit(database_url)
    query = parse_qsl(parsed.query, keep_blank_values=True)
    normalized = []
    for key, item_value in query:
        if key == "sslmode":
            if item_value in {"require", "verify-ca", "verify-full"}:
                normalized.append(("ssl", "require"))
            elif item_value in {"disable", "allow", "prefer"}:
                continue
            else:
                normalized.append((key, item_value))
        else:
            normalized.append((key, item_value))
    return urlunsplit(parsed._replace(query=urlencode(normalized)))
