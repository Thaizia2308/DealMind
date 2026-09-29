"""Application settings, loaded from environment variables / a .env file.

The .env file may live in the project root (DealMind/.env) or in backend/.env.
"""
from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

HINDSIGHT_CLOUD_URL = "https://api.hindsight.vectorize.io"
PLACEHOLDERS = {"", "your_key_here", "your-key-here", "changeme"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),  # relative to backend/ (where uvicorn runs)
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Hindsight (real memory) ---
    hindsight_api_key: Optional[str] = None
    # Leave empty to use Hindsight Cloud when an API key is set.
    # Set to http://localhost:8888 for a self-hosted Hindsight server.
    hindsight_base_url: Optional[str] = None
    hindsight_bank_prefix: str = "dealmind"
    hindsight_retain_async: bool = False
    hindsight_timeout: float = 120.0

    # --- App ---
    database_url: str = "sqlite:///./dealmind.db"
    # Comma-separated list of allowed browser origins (CORS).
    frontend_url: str = "http://localhost:5173"

    @field_validator("hindsight_api_key", "hindsight_base_url", mode="before")
    @classmethod
    def _blank_or_placeholder_is_unset(cls, v):
        if v is None:
            return None
        v = str(v).strip()
        return None if v.lower() in PLACEHOLDERS else v

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip().rstrip("/") for o in self.frontend_url.split(",") if o.strip()]

    @property
    def resolved_hindsight_url(self) -> Optional[str]:
        if self.hindsight_base_url and self.hindsight_base_url.strip():
            return self.hindsight_base_url.strip().rstrip("/")
        if self.hindsight_api_key and self.hindsight_api_key.strip():
            return HINDSIGHT_CLOUD_URL
        return None

    @property
    def hindsight_configured(self) -> bool:
        return self.resolved_hindsight_url is not None

    @property
    def hindsight_mode(self) -> str:
        url = self.resolved_hindsight_url
        if url is None:
            return "not-configured"
        return "cloud" if url == HINDSIGHT_CLOUD_URL else "self-hosted"


@lru_cache
def get_settings() -> Settings:
    return Settings()
