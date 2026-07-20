from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List
from fastapi_cache.decorator import cache

from app.database import get_db
from app.models import Starship
from app.schemas.schemas import StarshipResponse

router = APIRouter(prefix="/starships", tags=["Starships"])

@router.get("", response_model=List[StarshipResponse])
@cache(expire=60)
async def get_starships(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Retrieve starships with pagination."""
    query = select(Starship).options(selectinload(Starship.pilots)).offset(skip).limit(limit)
    result = await db.scalars(query)
    return result.unique().all()

@router.get("/search", response_model=List[StarshipResponse])
@cache(expire=60)
async def search_starships(name: str, db: AsyncSession = Depends(get_db)):
    """Search starships by name (case-insensitive partial match)."""
    query = select(Starship).options(selectinload(Starship.pilots)).where(func.lower(Starship.name).like(f"%{name.lower()}%"))
    result = await db.scalars(query)
    return result.unique().all()

@router.get("/{starship_id}", response_model=StarshipResponse)
@cache(expire=60)
async def get_starship(starship_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve a specific starship by ID."""
    query = select(Starship).options(selectinload(Starship.pilots)).where(Starship.id == starship_id)
    starship = await db.scalar(query)
    if not starship:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Starship not found")
    return starship
