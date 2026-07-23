"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validates and exposes all environment variables as typed attributes."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str

    # ── JWT ───────────────────────────────────────────────────
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── Gemini ────────────────────────────────────────────────
    GEMINI_API_KEY: str

    # ── CORS ──────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:4173,http://127.0.0.1:8000,https://workwell-wellness-platform.vercel.app"

    # ── Rate limiting ─────────────────────────────────────────
    LOGIN_RATE_LIMIT: int = 10
    LOGIN_RATE_WINDOW: int = 300

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Singleton accessor — parsed once per process."""
    return Settings()
