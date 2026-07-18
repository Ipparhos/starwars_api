# Star Wars API

A RESTful API that syncs Star Wars characters, films, and starships from
[SWAPI](https://swapi.dev/) into a local Postgres database, serves them back
with pagination, and lets you vote for your favorites.

## Design Decisions

**Python 3.12.13** — Chosen for ecosystem maturity: broad, stable
compatibility with SQLAlchemy, Alembic, httpx, and the async testing stack
used in this project. 3.12.13 is the latest patch release on the 3.12
branch, so it includes all bug fixes and security patches to date while
avoiding early-adopter friction from newer minor versions (e.g. 3.14).

**FastAPI over Django/Flask** — Selected for its native async support,
which fits the I/O-bound nature of proxying and caching data from an
external API (SWAPI). Pydantic gives request/response validation out of
the box, and FastAPI auto-generates OpenAPI/Swagger docs from the route
and schema definitions, directly satisfying the documentation requirement
with minimal extra overhead.

**SQLAlchemy 2.0 (async) + asyncpg** — Keeps the whole request path
non-blocking end to end: an incoming request can await both the DB and,
during sync, the outbound SWAPI call, without tying up a worker thread.

**SWAPI reliability handling** — `swapi.dev` is a community-run mirror,
not an official service, and has had documented outages historically. To
avoid that becoming this API's problem too:
- All SWAPI calls are isolated behind a single `SWAPIClient` class
  (`app/services/swapi_client.py`), so nothing else in the codebase talks
  to SWAPI directly.
- Requests retry with exponential backoff (`tenacity`, 3 attempts) before
  giving up.
- A failure after retries raises `SWAPIUnavailableError`, which a global
  exception handler turns into a `503` with a clear message — never a raw
  connection error or a `500`.
- Fetched data is persisted in the local DB rather than re-fetched on every
  read, so reads work fine even if SWAPI is down at the time.

**Voting** — The brief mentions voting once, without specifying its shape
(a counter? a table? per-user?). I implemented it as a separate `Vote`
table (`resource_type`, `resource_id`, `created_at`) rather than a bare
counter column, so there's an audit trail and room to build a "most
voted" leaderboard later, at the cost of a `COUNT()` query instead of a
column read on `GET /votes/{type}/{id}`. There's no auth layer, so voting
is currently unlimited per resource (no one-vote-per-user enforcement) —
see Known Limitations.

## Project Structure

```
app/
  main.py              # FastAPI app, exception handlers, router wiring
  config.py            # Settings via pydantic-settings (reads .env)
  database.py           # Async engine/session, Base, get_db dependency
  models/                # SQLAlchemy ORM models
  schemas/                # Pydantic request/response models
  services/
    swapi_client.py       # Isolated external-API layer (retry/backoff/errors)
    sync_service.py        # Fetches from SWAPI, upserts into DB
  routers/
    characters.py, films.py, starships.py, votes.py, sync.py
docker-compose.yml
Dockerfile
requirements.txt
```

## Prerequisites

- Docker + Docker Compose (recommended), **or**
- Python 3.12 and a local Postgres instance

## Setup & Run

### Option A — Docker Compose (recommended)

```bash
docker-compose up --build
```

This starts Postgres and the API together; the API waits for Postgres's
healthcheck before starting. Once running:

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Option B — Local virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # then edit DATABASE_URL to point at your local Postgres

uvicorn app.main:app --reload
```

### Populating data

The database starts empty — nothing is fetched automatically. Trigger a
sync via Swagger UI or curl:

```bash
# Recommended: syncs films, starships, then characters, in the order
# needed for relationships to resolve correctly
curl -X POST http://localhost:8000/api/sync

# Or one resource type at a time
curl -X POST http://localhost:8000/api/sync/films
curl -X POST http://localhost:8000/api/sync/starships
curl -X POST http://localhost:8000/api/sync/characters
```

Sync is idempotent — re-running it updates existing records by their
SWAPI id rather than creating duplicates.

## Environment Variables

See `.env.example`. In short: `DATABASE_URL` (Postgres connection string),
`SWAPI_BASE_URL`, and `SWAPI_TIMEOUT_SECONDS`.

## API Overview

| Method | Path | Description |
|---|---|---|
| POST | `/api/sync` | Sync films, starships, and characters from SWAPI |
| POST | `/api/sync/{films\|starships\|characters}` | Sync one resource type |
| GET | `/api/characters` | Paginated list of stored characters |
| GET | `/api/characters/{id}` | Get one character |
| GET | `/api/films` | Paginated list of stored films |
| GET | `/api/films/{id}` | Get one film |
| GET | `/api/starships` | Paginated list of stored starships |
| GET | `/api/starships/{id}` | Get one starship |
| POST | `/api/votes/{type}/{id}` | Cast a vote for a character/film/starship |
| GET | `/api/votes/{type}/{id}` | Get a resource's vote count |
| GET | `/health` | Liveness check |

Full interactive documentation, including request/response schemas and
field-level descriptions, is at `/docs` once the app is running.

## Error Handling

| Status | When |
|---|---|
| 404 | Resource id doesn't exist |
| 409 | Database integrity error (e.g. a race on a unique constraint) |
| 422 | Invalid input (e.g. bad `resource_type`, out-of-range pagination params) — handled automatically by FastAPI/Pydantic |
| 503 | SWAPI unreachable after retries |
| 500 | Anything unexpected — caught by a global handler so no stack trace leaks to the client |

## Testing

**Status: not yet implemented.** Planned approach, to be added next:

- `pytest` + `pytest-asyncio`, with SWAPI calls mocked via `respx` (tests
  never hit the real SWAPI)
- An in-memory SQLite database per test session (already validated as
  working against these models and the sync service during development)
- Coverage target: 80%, verified via
  `pytest --cov=app --cov-report=term-missing`
- Planned coverage: sync (success + SWAPI-down → 503), pagination,
  voting, and validation-error cases

## Known Limitations / Roadmap

Being upfront about what's not done yet, rather than silently shipping
around it:

- **No migrations yet.** There's no Alembic setup and nothing currently
  calls `create_all()` on startup, so tables must be created manually for
  now. Alembic migrations are the next planned addition — this is a
  correctness gap, not a stylistic one.
- **No search-by-name endpoint yet.** Listed as a requirement; not yet
  implemented. Planned as `GET /{resource}/search?name=...`,
  case-insensitive partial match.
- **No automated tests yet** — see Testing above.
- **No auth.** Sync and vote endpoints are unauthenticated; anyone with
  network access can trigger a sync or vote. Acceptable for a take-home
  assessment scope, but would need an API key or JWT on mutating
  endpoints before this went anywhere near production.
