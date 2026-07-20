from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List
from fastapi import Query
from fastapi_cache.decorator import cache

from app.database import get_db
from app.models import Film
from app.schemas.schemas import FilmResponse, PaginatedResponse

router = APIRouter(prefix="/films", tags=["Films"])

@router.get("", response_model=PaginatedResponse[FilmResponse])
@cache(expire=60)
async def get_films(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve films with pagination."""
    query = select(Film).options(selectinload(Film.characters)).offset(skip).limit(limit)
    result = await db.scalars(query)
    data = [FilmResponse.model_validate(f) for f in result.unique().all()]
    return {"data": data, "skip": skip, "limit": limit}

@router.get("/search", response_model=List[FilmResponse])
@cache(expire=60)
async def search_films(title: str, db: AsyncSession = Depends(get_db)):
    """Search films by title (case-insensitive partial match)."""
    title_escaped = title.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    query = select(Film).options(selectinload(Film.characters)).where(func.lower(Film.title).like(f"%{title_escaped}%", escape="\\"))
    result = await db.scalars(query)
    return [FilmResponse.model_validate(f) for f in result.unique().all()]

@router.get("/{film_id}", response_model=FilmResponse)
@cache(expire=60)
async def get_film(film_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve a specific film by ID."""
    query = select(Film).options(selectinload(Film.characters)).where(Film.id == film_id)
    film = await db.scalar(query)
    if not film:
        raise HTTPException(status_code=404, detail=f"Film with ID {film_id} not found")
    return FilmResponse.model_validate(film)
