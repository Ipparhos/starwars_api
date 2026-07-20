from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_cache.decorator import cache

from app.database import get_db
from app.models import Vote, Character, Film, Starship
from app.schemas.schemas import VoteCreate, VoteResponse, VoteCount

router = APIRouter(prefix="/votes", tags=["Votes"])

@router.get("/{resource_type}/{resource_id}", response_model=VoteCount)
@cache(expire=60)
async def get_vote_count(resource_type: str, resource_id: int, db: AsyncSession = Depends(get_db)):
    """Get the total number of votes for a specific resource."""
    resource_type = resource_type.lower()
    
    if resource_type not in ["character", "film", "starship"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail="resource_type must be 'character', 'film', or 'starship'"
        )
        
    query = select(func.count()).select_from(Vote).where(
        Vote.resource_type == resource_type,
        Vote.resource_id == resource_id
    )
    count = await db.scalar(query)
    
    resource_name = None
    if resource_type == "character":
        resource = await db.get(Character, resource_id)
        if resource: resource_name = resource.name
    elif resource_type == "film":
        resource = await db.get(Film, resource_id)
        if resource: resource_name = resource.title
    elif resource_type == "starship":
        resource = await db.get(Starship, resource_id)
        if resource: resource_name = resource.name
    
    return VoteCount(
        resource_type=resource_type,
        resource_id=resource_id,
        count=count or 0,
        resource_name=resource_name
    )

@router.post("", response_model=VoteResponse, status_code=status.HTTP_201_CREATED)
async def cast_vote(vote_in: VoteCreate, db: AsyncSession = Depends(get_db)):
    """Cast a vote for a character, film, or starship."""
    
    resource_type = vote_in.resource_type.lower()
    
    # Validate resource type and existence
    if resource_type == "character":
        resource = await db.get(Character, vote_in.resource_id)
    elif resource_type == "film":
        resource = await db.get(Film, vote_in.resource_id)
    elif resource_type == "starship":
        resource = await db.get(Starship, vote_in.resource_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail="resource_type must be 'character', 'film', or 'starship'"
        )
        
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"{resource_type.capitalize()} with ID {vote_in.resource_id} not found."
        )

    # Record the vote
    new_vote = Vote(resource_type=resource_type, resource_id=vote_in.resource_id)
    db.add(new_vote)
    await db.commit()
    await db.refresh(new_vote)
    
    return new_vote
