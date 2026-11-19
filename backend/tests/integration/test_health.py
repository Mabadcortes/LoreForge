from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.config import Settings
from app.db.session import get_session
from app.main import create_app


class FakeSession:
    """Stands in for AsyncSession: succeeds, or raises the given error."""

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error

    async def execute(self, statement: object) -> None:
        if self.error is not None:
            raise self.error


def make_client(settings: Settings, session: FakeSession) -> TestClient:
    app = create_app(settings)

    async def override_get_session() -> AsyncIterator[FakeSession]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    # Not used as a context manager, so the lifespan (real engine) never runs.
    return TestClient(app)


def test_health_returns_200_when_database_is_reachable(settings: Settings) -> None:
    client = make_client(settings, FakeSession())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_returns_503_with_generic_body_when_database_is_down(
    settings: Settings, caplog: pytest.LogCaptureFixture
) -> None:
    driver_error = OperationalError(
        "SELECT 1", {}, Exception('password authentication failed for user "loreforge"')
    )
    client = make_client(settings, FakeSession(error=driver_error))

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unavailable"}
    # The internal detail must reach the log but never the client.
    assert "password authentication failed" not in response.text
    assert "password authentication failed" in caplog.text


def test_cors_allows_configured_origin(settings: Settings) -> None:
    client = make_client(settings, FakeSession())

    response = client.get("/health", headers={"Origin": "http://localhost:3000"})

    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
