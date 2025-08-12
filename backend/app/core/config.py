import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get project root (one level above "backend")
# __file__ -> backend/app/core/config.py; parents[3] -> project root directory
BASE_DIR = Path(__file__).resolve().parents[3]
ENV_PATH = str(BASE_DIR / ".env")

class Settings(BaseSettings):
    # pydantic-settings v2 configuration
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str
    HUGGINGFACE_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    HUGGINGFACEHUB_API_TOKEN: str | None = None

settings = Settings()
