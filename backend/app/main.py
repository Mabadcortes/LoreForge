"""FastAPI application factory.

Run with:
    uv run uvicorn app.main:create_app --factory --reload --loop asyncio:SelectorEventLoop

`--loop asyncio:SelectorEventLoop` is required on Windows: uvicorn may otherwise
pick the ProactorEventLoop, which psycopg async cannot use. It is harmless on
Linux, where SelectorEventLoop is already the default. See ADR 0001.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health
from app.core.config import Settings, get_settings
from app.db.session import create_db_engine, create_session_factory


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the app. Tests pass their own settings; production reads the env."""
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Creating the engine does not connect yet; connections open lazily.
        engine = create_db_engine(app_settings)
        app.state.session_factory = create_session_factory(engine)
        yield
        await engine.dispose()

    app = FastAPI(title="LoreForge API", version="0.0.1", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)

    return app
