from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Character, Film, Starship, Vote
from app.schemas import VoteCount, VoteResponse


class ResourceType(str, Enum):
    character = "character"
    film = "film"
    starship = "starship"


_MODEL_MAP = {
    ResourceType.character: Character,
    ResourceType.film: Film,
    ResourceType.starship: Starship,
}

router = APIRouter(prefix="/votes", tags=["votes"])


async def _get_resource_or_404(db: AsyncSession, resource_type: ResourceType, resource_id: int):
    model = _MODEL_MAP[resource_type]
    resource = await db.get(model, resource_id)
    if resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_type.value.capitalize()} not found",
        )
    return resource


@router.post(
    "/{resource_type}/{resource_id}",
    response_model=VoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cast a vote",
    description=(
        "Casts one vote for a character, film, or starship by its local id "
        "(not its SWAPI id). Each call records a new vote row — there's no "
        "one-vote-per-user limit, since this API has no auth/identity layer."
    ),
    responses={404: {"description": "No resource of that type with that id"}},
)
async def create_vote(
    resource_type: ResourceType, resource_id: int, db: AsyncSession = Depends(get_db)
):
    await _get_resource_or_404(db, resource_type, resource_id)
    vote = Vote(resource_type=resource_type.value, resource_id=resource_id)
    db.add(vote)
    await db.commit()
    await db.refresh(vote)
    return vote


@router.get(
    "/{resource_type}/{resource_id}",
    response_model=VoteCount,
    summary="Get a resource's vote count",
    responses={404: {"description": "No resource of that type with that id"}},
)
async def get_vote_count(
    resource_type: ResourceType, resource_id: int, db: AsyncSession = Depends(get_db)
):
    await _get_resource_or_404(db, resource_type, resource_id)
    count = await db.scalar(
        select(func.count()).select_from(Vote).where(
            Vote.resource_type == resource_type.value,
            Vote.resource_id == resource_id,
        )
    )
    return {
        "resource_type": resource_type.value,
        "resource_id": resource_id,
        "vote_count": count or 0,
    }
