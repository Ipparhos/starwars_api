from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.sync_service import SyncService
from app.services.swapi_client import SWAPIClient

router = APIRouter(tags=["Sync"])

@router.post("/sync", status_code=status.HTTP_202_ACCEPTED)
async def sync_data(db: AsyncSession = Depends(get_db)):
    """
    Trigger a manual synchronization with the Star Wars API (SWAPI).
    Fetches all films, starships, and characters, resolving relationships, and upserts them into the database.
    """
    client = SWAPIClient()
    service = SyncService(db=db, client=client)
    
    # We are keeping it simple per requirements, so we await it here.
    results = await service.sync_all()
    return {"message": "Sync completed successfully", "details": results}
