from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    database_url: str = Field(default="sqlite:///../data/skillsprint.db")
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    upload_dir: Path = Path("../data/uploads")
    max_upload_bytes: int = 15 * 1024 * 1024
    jwt_secret: str = "change-this-before-deployment"
    jwt_expiry_minutes: int = 480
    generation_mode: str = "auto"  # "auto" (live OpenAI when key present) or "mock" (deterministic, offline)


@lru_cache
def get_settings() -> Settings:
    return Settings()
