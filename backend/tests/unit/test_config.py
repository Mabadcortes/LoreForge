import pytest

from app.core.config import Settings

REQUIRED = {"postgres_user": "user", "postgres_password": "secret", "postgres_db": "db"}


def make_settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **{**REQUIRED, **overrides})  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("http://localhost:3000", ["http://localhost:3000"]),
        (
            "http://localhost:3000, http://127.0.0.1:3000",
            ["http://localhost:3000", "http://127.0.0.1:3000"],
        ),
        ("http://localhost:3000,", ["http://localhost:3000"]),
        ("", []),
    ],
)
def test_cors_origins_are_read_as_comma_separated_list(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: list[str]
) -> None:
    monkeypatch.setenv("CORS_ORIGINS", raw)

    assert make_settings().cors_origins == expected


def test_database_url_is_built_from_postgres_parts() -> None:
    settings = make_settings(postgres_host="db", postgres_port=5433)

    url = settings.database_url

    assert url.drivername == "postgresql+psycopg"
    assert url.username == "user"
    assert url.password == "secret"
    assert url.host == "db"
    assert url.port == 5433
    assert url.database == "db"


def test_database_url_escapes_special_characters_in_password() -> None:
    settings = make_settings(postgres_password="p@ss/w:rd")

    rendered = settings.database_url.render_as_string(hide_password=False)

    assert "p%40ss%2Fw%3Ard@" in rendered
    assert settings.database_url.password == "p@ss/w:rd"


def test_password_is_hidden_in_repr() -> None:
    settings = make_settings(postgres_password="top-secret")

    assert "top-secret" not in repr(settings)
