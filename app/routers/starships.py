from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List
from fastapi import Query
from fastapi_cache.decorator import cache

from app.database import get_db
from app.models import Starship
from app.schemas.schemas import StarshipResponse, PaginatedResponse

router = APIRouter(prefix="/starships", tags=["Starships"])

@router.get("", response_model=PaginatedResponse[StarshipResponse])
@cache(expire=60)
async def get_starships(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve starships with pagination."""
    query = select(Starship).options(selectinload(Starship.pilots)).offset(skip).limit(limit)
    result = await db.scalars(query)
    data = [StarshipResponse.model_validate(s) for s in result.unique().all()]
    return {"data": data, "skip": skip, "limit": limit}

@router.get("/search", response_model=List[StarshipResponse])
@cache(expire=60)
async def search_starships(name: str, db: AsyncSession = Depends(get_db)):
    """Search starships by name (case-insensitive partial match)."""
    name_escaped = name.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    query = select(Starship).options(selectinload(Starship.pilots)).where(func.lower(Starship.name).like(f"%{name_escaped}%", escape="\\"))
    result = await db.scalars(query)
    return [StarshipResponse.model_validate(s) for s in result.unique().all()]

@router.get("/{starship_id}", response_model=StarshipResponse)
@cache(expire=60)
async def get_starship(starship_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve a specific starship by ID."""
    query = select(Starship).options(selectinload(Starship.pilots)).where(Starship.id == starship_id)
    ship = await db.scalar(query)
    if not ship:
        raise HTTPException(status_code=404, detail=f"Starship with ID {starship_id} not found")
    return StarshipResponse.model_validate(ship)
