from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Character
from app.schemas import CharacterResponse, PaginatedCharacters

router = APIRouter(prefix="/characters", tags=["characters"])


@router.get(
    "",
    response_model=PaginatedCharacters,
    summary="List characters",
    description=(
        "Returns characters already stored in the local database, paginated. "
        "This does not call SWAPI — run POST /sync/characters first to populate data."
    ),
)
async def list_characters(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return (1-100)"),
    db: AsyncSession = Depends(get_db),
):
    count = await db.scalar(select(func.count()).select_from(Character))
    rows = await db.scalars(
        select(Character).order_by(Character.id).offset(skip).limit(limit)
    )
    return {"count": count or 0, "results": rows.all()}


@router.get(
    "/{character_id}",
    response_model=CharacterResponse,
    summary="Get a character by local id",
    responses={404: {"description": "Character not found"}},
)
async def get_character(character_id: int, db: AsyncSession = Depends(get_db)):
    character = await db.get(Character, character_id)
    if character is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Character not found"
        )
    return character
