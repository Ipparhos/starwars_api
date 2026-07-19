from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.database import get_db
from app.models import Film
from app.schemas.schemas import FilmResponse

router = APIRouter(prefix="/films", tags=["Films"])

@router.get("", response_model=List[FilmResponse])
async def get_films(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Retrieve films with pagination."""
    result = await db.scalars(select(Film).offset(skip).limit(limit))
    return result.all()

@router.get("/search", response_model=List[FilmResponse])
async def search_films(title: str, db: AsyncSession = Depends(get_db)):
    """Search films by title (case-insensitive partial match)."""
    query = select(Film).where(func.lower(Film.title).like(f"%{title.lower()}%"))
    result = await db.scalars(query)
    return result.all()

@router.get("/{film_id}", response_model=FilmResponse)
async def get_film(film_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve a specific film by ID."""
    film = await db.get(Film, film_id)
    if not film:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Film not found")
    return film
