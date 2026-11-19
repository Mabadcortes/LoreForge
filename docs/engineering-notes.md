# Engineering notes

Short write-ups of non-obvious problems found while building LoreForge: what
happened, why, how it was fixed and what I took away from it. Architecture-level
choices live in [Architecture Decision Records](adr/); this file is for the
lessons learned along the way.

Format: **Problem → Cause → Solution → Takeaway**. Newest first.

---

## 2026-11-19 · Async psycopg fails on Windows: ProactorEventLoop vs SelectorEventLoop

**Problem.** Running the backend on Windows against a real PostgreSQL database
failed with `Psycopg cannot use the 'ProactorEventLoop' to run in async mode`.
Inside Docker and in CI (Linux) everything worked.

**Cause.** Python's asyncio has two event loop implementations on Windows:
`ProactorEventLoop` (the default, based on IOCP) and `SelectorEventLoop` (based
on `select()`). Async psycopg 3 waits on the libpq socket with
`add_reader`/`add_writer`, which only the selector loop provides. Uvicorn picks
the Proactor loop on Windows unless it starts a subprocess (`--reload` or
`--workers`), so the error could appear or disappear depending on flags.

**Solution.** Choose the loop explicitly when starting the server:

```powershell
uv run uvicorn app.main:create_app --factory --reload --loop asyncio:SelectorEventLoop
```

Setting an event loop policy inside the application code does not work, because
uvicorn creates the loop before importing the app (and loop policies are
deprecated from Python 3.14). The command is documented in `app/main.py` and in
the VS Code launch configuration. On Linux the selector loop is already the
default, so the flag is harmless there.

**Takeaway.** "Works in Docker, fails on my machine" often comes from platform
defaults. Read the library's constraints (psycopg documents this one) and make
the requirement explicit instead of relying on a side effect of another flag.

---

## 2026-11-19 · Comma-separated `CORS_ORIGINS` rejected by pydantic-settings

**Problem.** `.env` contains `CORS_ORIGINS=http://localhost:3000`, and the
setting is typed as `list[str]`. Loading the settings failed with a JSON
decoding error.

**Cause.** For complex types such as lists, pydantic-settings parses environment
values as JSON by default, so it expects `["http://localhost:3000"]`.

**Solution.** Annotate the field with `NoDecode` to disable the JSON step and
split the string in a `field_validator(mode="before")`. Unit tests cover single
and multiple origins.

**Takeaway.** Environment variables are always strings; every non-string setting
needs an explicit, tested parsing rule. Keeping `.env` human-friendly is worth a
few lines of validation.

---

## 2026-11-19 · Building the database URL with `URL.create` instead of string formatting

**Problem.** The previous prototype stored the full connection string in a
`DATABASE_URL` variable, duplicating the password that was also in
`POSTGRES_PASSWORD`. Changing one and forgetting the other broke the connection.
Building the URL with an f-string would also break as soon as the password
contained characters such as `@` or `/`.

**Cause.** A connection URL has its own syntax: `@` separates credentials from
the host and `/` starts the database name, so these characters must be escaped.

**Solution.** The backend reads the individual `POSTGRES_*` variables and builds
the URL with `sqlalchemy.URL.create()`, which escapes every part. The password is
stored as a Pydantic `SecretStr`, so it is masked when the settings are printed
or logged. A unit test uses a password containing `@` and `/`.

**Takeaway.** Keep each piece of configuration in one place (DRY), build
structured values with the library meant for them, and test the edge cases that
string concatenation gets wrong.

---

## 2026-11-19 · Health check must not leak internal errors

**Problem.** The prototype's `/health` returned `"unreachable: <exception text>"`
with status 200 when the database was down.

**Cause.** Two separate mistakes: monitoring tools (and Kubernetes probes later)
read the **status code**, so a 200 hid the outage; and the exception message can
expose the host, user or driver details to anyone calling the endpoint.

**Solution.** `/health` runs `SELECT 1` and returns 200 when it works, or
**503 Service Unavailable** with a generic body when it does not. The full error
goes to the server log with `logger.exception`. Tests cover both cases by
overriding the session dependency, and check that the error text never reaches
the client.

**Takeaway.** Health endpoints are read by machines: the status code is the
contract. Log details for operators; give clients only what they need.

---

## 2026-11-19 · Deprecation warning in the test suite: httpx → httpx2

**Problem.** Every test run printed `StarletteDeprecationWarning: Using httpx
with starlette.testclient is deprecated; install httpx2 instead.`

**Cause.** Starlette (the framework under FastAPI) is moving its `TestClient`
to `httpx2` and warns when only the old `httpx` package is installed.

**Solution.** Replace `httpx` with `httpx2` in the development dependencies
(`uv remove --dev httpx; uv add --dev httpx2`). The suite now runs without
warnings.

**Takeaway.** Keep the test output clean. A suite that always shows warnings
teaches everyone to ignore them, which is exactly where a real deprecation will
hide.

---

## 2026-11-19 · Line endings: CRLF from Windows breaking Linux containers

**Problem (prevented).** Developing on Windows and running in Linux containers is
a classic source of errors such as `/bin/sh^M: bad interpreter`.

**Cause.** Windows ends lines with `\r\n` (CRLF), Linux with `\n` (LF). A shell
script checked out with CRLF fails inside a Linux container.

**Solution.** A `.gitattributes` file normalises every text file to LF in the
repository and in the working tree (`* text=auto eol=lf`), with exceptions for
Windows-only scripts (`*.ps1`, `*.bat`, `*.cmd`). `.editorconfig` and the VS Code
settings make editors write LF too. `.gitattributes` takes precedence over each
developer's `core.autocrlf` setting.

**Takeaway.** Cross-platform problems are cheapest to fix on day one, in the
repository itself, rather than in each developer's local configuration.
