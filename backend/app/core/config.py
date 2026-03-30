from functools import lru_cache

from pydantic import Field, PostgresDsn
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

    @property
    def cors_origins(self) -> list[str]:
        """Get CORS origins for middleware."""
        return self.BACKEND_CORS_ORIGINS or ["*"]

    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Logging
    LOG_LEVEL: str = "info"
    LOG_FORMAT: str = "json"

    # AI API
    ANTHROPIC_API_KEY: str = Field(default="")

    # Scheduler Configuration
    scheduler_enabled: bool = Field(default=True)
    kr_tickers: list[str] = Field(
        default=[
            "005930",  # 삼성전자
            "000660",  # SK하이닉스
            "035420",  # NAVER
            "005380",  # 현대차
            "000270",  # 기아
        ]
    )
    us_tickers: list[str] = Field(
        default=[
            "AAPL", "MSFT", "GOOGL",
            "AMZN", "NVDA",
        ]
    )
    
    # Missed Execution Recovery Configuration
    max_recovery_days: int = Field(default=3)

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
