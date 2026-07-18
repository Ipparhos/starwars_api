# starwars_api

## Design Decisions

**Python 3.12.13** — Chosen for ecosystem maturity: broad, stable compatibility
with SQLAlchemy, Alembic, httpx, and the async testing stack used in this
project. 3.12.13 is the latest patch release on the 3.12 branch, so it
includes all bug fixes and security patches to date while avoiding any
early-adopter friction from newer minor versions (e.g. 3.14).

**FastAPI over Django** — Selected for its native async support, which fits
the I/O-bound nature of proxying and caching data from an external API
(SWAPI). Pydantic gives request/response validation out of the box, and
FastAPI auto-generates OpenAPI/Swagger docs from the route and schema
definitions, directly satisfying the documentation requirement with minimal
extra overhead.