from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.database import get_db
from app.models import Character
from app.schemas.schemas import CharacterResponse

router = APIRouter(prefix="/characters", tags=["Characters"])

@router.get("", response_model=List[CharacterResponse])
async def get_characters(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Retrieve characters with pagination."""
    result = await db.scalars(select(Character).offset(skip).limit(limit))
    return result.all()

@router.get("/search", response_model=List[CharacterResponse])
async def search_characters(name: str, db: AsyncSession = Depends(get_db)):
    """Search characters by name (case-insensitive partial match)."""
    # Using func.lower() for case-insensitive partial match compatible with SQLite and Postgres
    query = select(Character).where(func.lower(Character.name).like(f"%{name.lower()}%"))
    result = await db.scalars(query)
    return result.all()

@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(character_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve a specific character by ID."""
    character = await db.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    return character
