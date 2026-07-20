from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from app.services.swapi_client import SWAPIUnavailableError
from app.routers import sync, characters, films, starships, votes

from contextlib import asynccontextmanager
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = aioredis.from_url(settings.REDIS_URL, encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    yield

app = FastAPI(
    title="Star Wars API",
    description="RESTful API for Star Wars characters, films, and starships.",
    version="1.0.0",
    lifespan=lifespan,
)

# Exception Handlers
@app.exception_handler(SWAPIUnavailableError)
async def swapi_unavailable_exception_handler(request: Request, exc: SWAPIUnavailableError):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "The external Star Wars API (SWAPI) is currently unreachable. Please try again later."},
    )

@app.exception_handler(IntegrityError)
async def sqlalchemy_integrity_exception_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "A database integrity error occurred (e.g., duplicate record)."},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the full stack trace internally here
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred."},
    )

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}

app.include_router(sync.router, prefix="/api")
app.include_router(characters.router, prefix="/api")
app.include_router(films.router, prefix="/api")
app.include_router(starships.router, prefix="/api")
app.include_router(votes.router, prefix="/api")
