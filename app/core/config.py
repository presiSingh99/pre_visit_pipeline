"""Application configuration loaded from environment / .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven settings.

    OPENAI_API_KEY is required at call time (not import time) so that
    schema-only tests and tooling can run without credentials.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    llm_timeout_seconds: float = 60.0
    llm_max_retries: int = 1  # retries on malformed/invalid LLM output


@lru_cache
def get_settings() -> Settings:
    return Settings()
