import pytest
from pydantic import SecretStr

from app.core.config import Settings


@pytest.fixture
def settings() -> Settings:
    """Explicit test settings: never reads the developer's .env file."""
    return Settings(
        _env_file=None,
        app_env="test",
        cors_origins=["http://localhost:3000"],
        postgres_user="test",
        postgres_password=SecretStr("test"),
        postgres_db="test",
    )
