from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Film
from app.schemas import FilmResponse, PaginatedFilms

router = APIRouter(prefix="/films", tags=["films"])


@router.get(
    "",
    response_model=PaginatedFilms,
    summary="List films",
    description=(
        "Returns films already stored in the local database, paginated. "
        "This does not call SWAPI — run POST /sync/films first to populate data."
    ),
)
async def list_films(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return (1-100)"),
    db: AsyncSession = Depends(get_db),
):
    count = await db.scalar(select(func.count()).select_from(Film))
    rows = await db.scalars(
        select(Film).order_by(Film.id).offset(skip).limit(limit)
    )
    return {"count": count or 0, "results": rows.all()}


@router.get(
    "/{film_id}",
    response_model=FilmResponse,
    summary="Get a film by local id",
    responses={404: {"description": "Film not found"}},
)
async def get_film(film_id: int, db: AsyncSession = Depends(get_db)):
    film = await db.get(Film, film_id)
    if film is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Film not found"
        )
    return film
