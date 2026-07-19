from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.database import get_db
from app.models import Starship
from app.schemas.schemas import StarshipResponse

router = APIRouter(prefix="/starships", tags=["Starships"])

@router.get("", response_model=List[StarshipResponse])
async def get_starships(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Retrieve starships with pagination."""
    result = await db.scalars(select(Starship).offset(skip).limit(limit))
    return result.all()

@router.get("/search", response_model=List[StarshipResponse])
async def search_starships(name: str, db: AsyncSession = Depends(get_db)):
    """Search starships by name (case-insensitive partial match)."""
    query = select(Starship).where(func.lower(Starship.name).like(f"%{name.lower()}%"))
    result = await db.scalars(query)
    return result.all()

@router.get("/{starship_id}", response_model=StarshipResponse)
async def get_starship(starship_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve a specific starship by ID."""
    starship = await db.get(Starship, starship_id)
    if not starship:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Starship not found")
    return starship
