"""
Application settings loaded from environment variables.
Pydantic-settings reads from the .env file in development.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    ANTHROPIC_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://finvoice:finvoice@localhost:5432/finvoice"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_db_url(cls, v: str) -> str:
        # Railway injects postgresql:// or postgres:// — both need +asyncpg for SQLAlchemy async.
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # Cache
    REDIS_URL: str = "redis://localhost:6379"

    # Account Aggregator — Finvu sandbox
    # JWT issued by Finvu after you email support@cookiejar.co.in with your public key.
    # Leave blank to use the built-in synthetic Indian transaction data fallback.
    FINVU_CLIENT_API_KEY: str = ""

    # Voice
    DEEPGRAM_API_KEY: str = ""

    # App
    SECRET_KEY: str = "change-me-in-production"
    ENVIRONMENT: str = "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def use_deepgram(self) -> bool:
        return self.is_production and bool(self.DEEPGRAM_API_KEY)


settings = Settings()
