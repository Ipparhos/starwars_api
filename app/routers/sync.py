import uuid
from fastapi import APIRouter, BackgroundTasks, status
import logging

from app import database
from app.services.sync_service import SyncService
from app.services.swapi_client import SWAPIClient
from fastapi_cache import FastAPICache

router = APIRouter(tags=["Sync"])
logger = logging.getLogger(__name__)

async def _run_sync_task(task_id: str, method_name: str):
    """Run a sync operation in a background task with its own database session."""
    backend = FastAPICache.get_backend()
    try:
        if backend:
            await backend.set(f"sync_status:{task_id}", "running", expire=3600)
        async with database.AsyncSessionLocal() as db:
            client = SWAPIClient()
            service = SyncService(db=db, client=client)
            method = getattr(service, method_name)
            await method()
            logger.info(f"Background sync task '{method_name}' ({task_id}) completed successfully.")
        if backend:
            await backend.set(f"sync_status:{task_id}", "completed", expire=3600)
    except Exception as e:
        logger.error(f"Background sync task '{method_name}' ({task_id}) failed: {e}")
        if backend:
            await backend.set(f"sync_status:{task_id}", f"failed", expire=3600)

@router.post("/sync", status_code=status.HTTP_202_ACCEPTED)
async def sync_data(background_tasks: BackgroundTasks):
    """Trigger a manual synchronization with the Star Wars API (SWAPI) in the background."""
    task_id = str(uuid.uuid4())
    background_tasks.add_task(_run_sync_task, task_id, "sync_all")
    return {"message": "Sync started in the background", "task_id": task_id}

@router.post("/sync/films", status_code=status.HTTP_202_ACCEPTED)
async def sync_films(background_tasks: BackgroundTasks):
    """Sync only films from SWAPI in the background."""
    task_id = str(uuid.uuid4())
    background_tasks.add_task(_run_sync_task, task_id, "sync_films")
    return {"message": "Films sync started in the background", "task_id": task_id}

@router.post("/sync/starships", status_code=status.HTTP_202_ACCEPTED)
async def sync_starships(background_tasks: BackgroundTasks):
    """Sync only starships from SWAPI in the background."""
    task_id = str(uuid.uuid4())
    background_tasks.add_task(_run_sync_task, task_id, "sync_starships")
    return {"message": "Starships sync started in the background", "task_id": task_id}

@router.post("/sync/characters", status_code=status.HTTP_202_ACCEPTED)
async def sync_characters(background_tasks: BackgroundTasks):
    """Sync only characters from SWAPI in the background."""
    task_id = str(uuid.uuid4())
    background_tasks.add_task(_run_sync_task, task_id, "sync_characters")
    return {"message": "Characters sync started in the background", "task_id": task_id}

@router.get("/sync/status/{task_id}")
async def get_sync_status(task_id: str):
    """Check the status of a background sync task."""
    backend = FastAPICache.get_backend()
    if backend:
        status_val = await backend.get(f"sync_status:{task_id}")
        if status_val:
            if isinstance(status_val, bytes):
                status_val = status_val.decode('utf-8')
            return {"task_id": task_id, "status": status_val}
    return {"task_id": task_id, "status": "unknown"}
