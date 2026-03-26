from functools import lru_cache

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_ENV: str = "development"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str

    # Database
    DATABASE_URL: PostgresDsn
    DATABASE_TEST_URL: PostgresDsn | None = None  # For test database

    # PostgreSQL
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_TEST_DB: str = "pavlov_test"

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = []

    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Logging
    LOG_LEVEL: str = "info"
    LOG_FORMAT: str = "json"

    # External APIs (optional for future use)
    ALPHA_VANTAGE_API_KEY: str | None = None
    POLYGON_API_KEY: str | None = None
    IEX_CLOUD_API_KEY: str | None = None

    # Caching (optional for future use)
    REDIS_URL: str | None = None

    # Email (optional for future use)
    SMTP_TLS: bool = True
    SMTP_PORT: int | None = None
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None

    # Monitoring (optional for future use)
    SENTRY_DSN: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
