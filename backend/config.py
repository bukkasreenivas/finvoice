"""
Application settings loaded from environment variables.
Pydantic-settings reads from the .env file in development.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    ANTHROPIC_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://finvoice:finvoice@localhost:5432/finvoice"

    # Cache
    REDIS_URL: str = "redis://localhost:6379"

    # Account Aggregator
    FINVU_CLIENT_ID: str = ""
    FINVU_CLIENT_SECRET: str = ""
    AA_ENV: str = "sandbox"

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
