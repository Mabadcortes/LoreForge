# ADR 0001: Async database access with SQLAlchemy and psycopg 3

- **Status:** Accepted
- **Date:** 2026-11-19

## Context

The backend is FastAPI on PostgreSQL 16. Upcoming features are I/O-bound and
long-lived: narration is streamed with Server-Sent Events while the AI Director
waits on LLM API calls and runs several database queries per turn. We must
choose between synchronous and asynchronous database access, and a driver.

## Decision

- Use **SQLAlchemy 2.0 with `AsyncSession`** in the application.
- Use **psycopg 3** (`postgresql+psycopg`) as the only PostgreSQL driver. The same
  driver supports both async (application) and sync (Alembic migrations) modes.
- Alembic migrations run with a **synchronous** engine: they are a one-off CLI
  process and gain nothing from async.
- The engine is created in the FastAPI lifespan and stored in `app.state`; no
  engine is created at import time. Requests get a session through the
  `get_session` dependency.

## Alternatives considered

- **Sync SQLAlchemy**: simpler mental model, and FastAPI runs sync endpoints in a
  thread pool. Rejected because SSE streams and LLM calls would hold threads for
  seconds each, and mixing sync DB code into async streaming endpoints is awkward.
- **asyncpg**: fastest async driver, but async-only, so Alembic would need a
  second driver (or an async `env.py`). psycopg 3 covers both with one dependency.

## Consequences

- Lazy loading is not allowed in async code: relationships must be loaded
  explicitly (`selectinload`, `joinedload`), and sessions use
  `expire_on_commit=False`.
- **Windows:** psycopg async cannot run on the default `ProactorEventLoop`. Code
  that touches a real database with async psycopg on Windows must use a
  `SelectorEventLoop`. Docker (Linux) and CI are not affected.
- Tests replace `get_session` via `app.dependency_overrides`, so API tests do not
  need a database; real-database tests run in CI with a Postgres service.
