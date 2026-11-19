"""Application settings, loaded only from environment variables (12-Factor)."""

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy import URL

# Repository root .env (backend/app/core/config.py -> parents[3]). Optional:
# in Docker and CI the variables come from the real environment instead.
ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        # The shared .env also holds frontend variables (NEXT_PUBLIC_*).
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"

    # NoDecode disables pydantic-settings' default JSON parsing for complex
    # types, so "http://a,http://b" reaches the validator below as a string.
    cors_origins: Annotated[list[str], NoDecode] = []

    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_comma_separated(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def database_url(self) -> URL:
        """SQLAlchemy URL built from the POSTGRES_* parts.

        URL.create escapes special characters (e.g. '@' or '/' in the password),
        which naive string formatting would get wrong.
        """
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings, read once from the environment."""
    return Settings()
