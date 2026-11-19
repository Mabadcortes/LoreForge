# CLAUDE.md — LoreForge

This file gives Claude Code the context it needs at the start of every session.
Keep it up to date when a decision changes.

## What LoreForge is

A **local web app to play solo Dungeons & Dragons campaigns** with an AI acting as
Dungeon Master and a story that is never forgotten. It is also the owner's
**learning project and portfolio piece** to land a **full stack + AI developer job
in Ireland**, so code quality, tests, documentation and Git history matter as much
as features.

- Repository: https://github.com/Mabadcortes/LoreForge
- The previous prototype (built with another AI, with bugs) is kept in tag
  `v0-prototype`. `main` restarts from scratch. Do not reuse prototype code.
- Full design document (for the human; not readable from Claude Code):
  https://claude.ai/artifact/DJjaxSyoGTRedLkmYbRjd3

## How to work with me (most important section)

I am learning backend, frontend and architecture with this project.

1. **Explain in Spanish.** All explanations, plans and questions to me go in
   Spanish. Code, comments, commit messages, README and docs stay in English.
2. **Plan before writing.** Before creating or changing files, tell me which files
   you will touch, what each one does and how it fits the architecture. Wait for my
   OK before writing.
3. **Teach as you go.** After writing a file, explain the important blocks and *why*
   they are designed that way (alternatives, trade-offs, what an interviewer might ask).
4. **Small steps.** One logical change at a time, each ending in a working state.
5. **Never commit or push without asking.** Suggest the commit message
   (Conventional Commits) and let me run or approve it. Commits must be mine.
6. **Verify.** Run the relevant tests, linters and type checks after each change and
   show me the result. If something fails, explain the cause before fixing it.
7. **No secrets in Git.** Never write real keys or passwords into tracked files.

## Design principles (non-negotiable)

1. **The player rules.** If the player asks for something against the rules, the AI
   warns which rule is broken and does it anyway. Technically: the tool is called with
   `override=true`; the engine applies the effect without the check and logs it.
2. **The engine decides the numbers.** Dice, damage, HP, spell slots and conditions are
   always computed in Python and stored in PostgreSQL. The LLM never invents a roll;
   it calls engine tools and narrates their exact results.
3. **The story persists.** At campaign creation the AI turns the player's premise into
   a structured, versioned **campaign bible** (canon). Deviations go through
   `propose_canon_change` and are recorded with their reason.
4. **The AI is a full DM:** narration, NPCs, world, encounters — always via tools.

## Decisions already taken

| Area | Decision |
| --- | --- |
| Language | Code, commits, docs and **UI in English**. Chat narration language configurable per campaign (Spanish by default). |
| Rules | D&D 2024 rules ("5.5") from **SRD 5.2.1** (CC-BY-4.0, attribution required). Missing content = homebrew. |
| Backend | Python 3.11, FastAPI, Pydantic v2 + pydantic-settings, SQLAlchemy 2.0, **Alembic from day 1** (never `create_all()`). |
| Database | PostgreSQL 16 + pgvector (`pgvector/pgvector:pg16`). |
| Frontend | **Next.js (App Router) + React + TypeScript**, used **only as frontend**; FastAPI is the only backend. Tailwind CSS + shadcn/ui, TanStack Query. |
| Streaming | Server-Sent Events (SSE) for narration. |
| AI | Cloud APIs in **mixed mode** via `ModelRouter` behind an `LLMProvider` interface: premium model (Claude Sonnet 5.5 or gpt-6-sol) for the campaign bible and key scenes; cheap model (Claude Haiku 5.5 or gpt-6-luna) for routine narration and internal tasks. Final choice in phase 3. Monthly budget cap (80% → everything cheap). Tests use a fake provider. |
| Cost tracking | Every LLM call stored in `LLMCall` (model, purpose, tokens in/cached/out, latency, cost) linked to a `ContextSnapshot`. "Usage" screen + context inspector. |
| Dice | Server-side RNG (`secrets.SystemRandom`, seedable in tests). Modes: interactive (default), automatic, physical dice. Director uses `request_roll` and the turn pauses until the player rolls. Free dice tray (`2d6+3`, `4d6kh3`), hidden DM rolls, roll history with stats. |
| Memory | Structured state, lorebook cards triggered by name, plot compass, extracted facts, hierarchical summaries, hybrid RAG (pgvector + full-text), `recall`/`note_fact` tools, coherence checker, memory evals. |
| Quality | pytest, Vitest, Playwright, ruff, mypy, ESLint, Prettier, pre-commit, GitHub Actions. |
| Infra | Docker Compose for development; Kubernetes + Helm in phase 7. |
| License | MIT. |

## Target repository structure

```text
backend/
  app/
    main.py            # creates the FastAPI app, registers routers
    core/              # settings (pydantic-settings), logging, errors
    db/                # engine, session, Base
    models/            # ORM models, one file per entity
    schemas/           # Pydantic API contracts
    api/routes/        # thin HTTP endpoints: validate and delegate
    services/          # use cases (create campaign, play turn...)
    repositories/      # database queries
    rules/             # pure D&D engine: dice, checks, combat, spells...
    ai/                # providers/, tools/, prompts/, director.py, memory.py
  alembic/
  data/srd/            # SRD 5.2.1 content (JSON)
  tests/               # unit/ (rules), integration/ (API + DB)
  pyproject.toml
  Dockerfile
frontend/              # Next.js app
deploy/helm/           # phase 7
docs/                  # Architecture Decision Records (ADR)
.github/workflows/
docker-compose.yml
.env.example
README.md
```

**Dependency rule:** `api` → `services` → `repositories`, `rules`, `ai`.
`rules` depends on nothing (pure functions, fully unit-tested, no DB, no HTTP).

## Conventions

- Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`, `ci:`.
- Python: type hints everywhere, ruff format + lint, mypy clean, 4-space indent.
- TypeScript: strict mode, ESLint + Prettier, 2-space indent.
- Line endings: LF everywhere (`.gitattributes`), except `*.ps1/*.bat/*.cmd`.
- Configuration only through environment variables (12-Factor). `.env` is never
  committed; `.env.example` lists every variable. The backend builds the database URL
  from `POSTGRES_*` parts (no duplicated `DATABASE_URL`).
- Every important decision gets a short ADR in `docs/adr/`.

## Development environment (Windows)

- Windows + Docker Desktop (WSL2), Docker 29.9.3, Compose v5.7.0, Git 2.56.0,
  VS Code 1.146.0. Shell: PowerShell.
- Python: use `py -3.11` (Python 3.13 is also installed; plain `python` may be 3.13).
- **A native Windows PostgreSQL 17 service (`postgresql-x64-17`) exists.** It is
  stopped and set to Manual so the `db` container can use port 5432. If the container
  fails with "port is already allocated", check that service first.

## Roadmap

| Phase | Scope | Status |
| --- | --- | --- |
| 0 · Foundations | Repo config, backend skeleton (`/health` returning 503 when DB is down), Alembic, first tests, Next.js skeleton, docker-compose with healthchecks, GitHub Actions, README, tag `v0.0.1` | **In progress** |
| 1 · Full stack skeleton | Home screen, campaigns & characters API, typed API client | |
| 2 · Characters & rules engine | SRD 5.2.1 data, character wizard, full sheet, checks, dice tray | |
| 3 · AI Director | Campaign bible, game table, tool calling, `request_roll`, SSE, lorebook, plot compass, `ModelRouter`, usage screen | |
| 4 · Memory | Facts, summaries, hybrid RAG, memory tools, coherence checker, editable journal, memory evals | |
| 5 · Full rules | Combat, attacks, conditions, death saves, inventory, spells, rests | |
| 6 · Images & map | Generated portraits/scenes, gallery, grid combat map, 3D dice | |
| 7 · Deployment | Helm chart on local Kubernetes, optional cloud demo | |

### Phase 0 progress

1. [x] Tag prototype as `v0-prototype`, clear `main`
2. [x] Root files: `.gitignore`, `.gitattributes`, `.editorconfig`, `.env.example`, `LICENSE`, `.vscode/`, `CLAUDE.md`
3. [ ] Backend skeleton: FastAPI + `/health`, settings, DB session, Alembic, pytest, ruff, mypy (`pyproject.toml`)
4. [ ] Frontend skeleton: Next.js + TypeScript + Tailwind + ESLint, page calling `/health`
5. [ ] `docker-compose.yml`: `db`, `backend`, `frontend` with healthchecks and hot reload
6. [ ] GitHub Actions: lint, type check, tests (backend with a Postgres service), frontend build
7. [ ] README in English + tag `v0.0.1`

Update this checklist as steps are completed.
