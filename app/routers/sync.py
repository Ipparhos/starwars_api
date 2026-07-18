from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import SyncResult
from app.services.sync_service import SyncService

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post(
    "",
    response_model=list[SyncResult],
    summary="Sync everything from SWAPI",
    description=(
        "Fetches all pages of films, starships, and characters from SWAPI and "
        "upserts them into the local database, in that order — films and "
        "starships must exist first so character relationships can be resolved "
        "against them. Safe to re-run: existing records are updated in place, "
        "not duplicated. Returns 503 if SWAPI is unreachable after retries."
    ),
)
async def sync_all(db: AsyncSession = Depends(get_db)):
    return await SyncService(db).sync_all()


@router.post(
    "/films",
    response_model=SyncResult,
    summary="Sync films from SWAPI",
)
async def sync_films(db: AsyncSession = Depends(get_db)):
    return await SyncService(db).sync_films()


@router.post(
    "/starships",
    response_model=SyncResult,
    summary="Sync starships from SWAPI",
)
async def sync_starships(db: AsyncSession = Depends(get_db)):
    return await SyncService(db).sync_starships()


@router.post(
    "/characters",
    response_model=SyncResult,
    summary="Sync characters from SWAPI",
    description=(
        "Run /sync/films and /sync/starships first — character film/starship "
        "relationships are resolved by looking up already-synced records, so "
        "syncing characters first will leave those relationships empty."
    ),
)
async def sync_characters(db: AsyncSession = Depends(get_db)):
    return await SyncService(db).sync_characters()
