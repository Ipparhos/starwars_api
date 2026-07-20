from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List
from fastapi_cache.decorator import cache

from app.database import get_db
from app.models import Character
from app.schemas.schemas import CharacterResponse, PaginatedResponse

router = APIRouter(prefix="/characters", tags=["Characters"])

@router.get("", response_model=PaginatedResponse[CharacterResponse])
@cache(expire=60)
async def get_characters(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Retrieve characters with pagination."""
    query = select(Character).options(selectinload(Character.films), selectinload(Character.starships)).offset(skip).limit(limit)
    result = await db.scalars(query)
    data = [CharacterResponse.model_validate(c) for c in result.unique().all()]
    return {"data": data, "skip": skip, "limit": limit}

@router.get("/search", response_model=List[CharacterResponse])
@cache(expire=60)
async def search_characters(name: str, db: AsyncSession = Depends(get_db)):
    """Search characters by name (case-insensitive partial match)."""
    name_escaped = name.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    # Using func.lower() for case-insensitive partial match compatible with SQLite and Postgres
    query = select(Character).options(selectinload(Character.films), selectinload(Character.starships)).where(func.lower(Character.name).like(f"%{name_escaped}%", escape="\\"))
    result = await db.scalars(query)
    return [CharacterResponse.model_validate(c) for c in result.unique().all()]

@router.get("/{character_id}", response_model=CharacterResponse)
@cache(expire=60)
async def get_character(character_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve a specific character by ID."""
    query = select(Character).options(selectinload(Character.films), selectinload(Character.starships)).where(Character.id == character_id)
    char = await db.scalar(query)
    if not char:
        raise HTTPException(status_code=404, detail=f"Character with ID {character_id} not found")
    return CharacterResponse.model_validate(char)
