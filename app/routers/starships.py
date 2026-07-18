from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Starship
from app.schemas import StarshipResponse, PaginatedStarships

router = APIRouter(prefix="/starships", tags=["starships"])


@router.get(
    "",
    response_model=PaginatedStarships,
    summary="List starships",
    description=(
        "Returns starships already stored in the local database, paginated. "
        "This does not call SWAPI — run POST /sync/starships first to populate data."
    ),
)
async def list_starships(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return (1-100)"),
    db: AsyncSession = Depends(get_db),
):
    count = await db.scalar(select(func.count()).select_from(Starship))
    rows = await db.scalars(
        select(Starship).order_by(Starship.id).offset(skip).limit(limit)
    )
    return {"count": count or 0, "results": rows.all()}


@router.get(
    "/{starship_id}",
    response_model=StarshipResponse,
    summary="Get a starship by local id",
    responses={404: {"description": "Starship not found"}},
)
async def get_starship(starship_id: int, db: AsyncSession = Depends(get_db)):
    starship = await db.get(Starship, starship_id)
    if starship is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Starship not found"
        )
    return starship
