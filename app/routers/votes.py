from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Vote, Character, Film, Starship
from app.schemas.schemas import VoteCreate, VoteResponse

router = APIRouter(prefix="/votes", tags=["Votes"])

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
