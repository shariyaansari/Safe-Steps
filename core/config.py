from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────
    database_url: str

    # ── JWT ───────────────────────────────────────────────
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # ── App ───────────────────────────────────────────────
    app_name: str = "Safe Steps"
    debug: bool = False

    # ── Redis ─────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379"

    # ── Media ─────────────────────────────────────────────
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,       # DATABASE_URL and database_url both work
        extra="ignore"              # silently ignore unrecognised env vars
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


# single import-friendly alias used across the codebase
# from core.config import settings
settings = get_settings()