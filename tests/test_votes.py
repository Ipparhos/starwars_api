import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Character, Vote

pytestmark = pytest.mark.asyncio

async def seed_data(db_session: AsyncSession) -> Character:
    char = Character(swapi_id=1, swapi_url="https://swapi.dev/api/people/1/", name="Luke Skywalker")
    db_session.add(char)
    await db_session.commit()
    await db_session.refresh(char)
    return char

async def test_cast_vote_success(async_client: AsyncClient, db_session: AsyncSession):
    """Test casting a successful vote."""
    char = await seed_data(db_session)
    
    payload = {
        "resource_type": "character",
        "resource_id": char.id
    }
    resp = await async_client.post("/api/votes", json=payload)
    assert resp.status_code == 201
    
    data = resp.json()
    assert data["resource_type"] == "character"
    assert data["resource_id"] == char.id
    
    # Verify in DB
    vote = await db_session.scalar(select(Vote))
    assert vote is not None
    assert vote.resource_id == char.id

async def test_cast_vote_validation_error(async_client: AsyncClient):
    """Test casting a vote with an invalid resource type."""
    payload = {
        "resource_type": "planet", # Invalid!
        "resource_id": 1
    }
    resp = await async_client.post("/api/votes", json=payload)
    assert resp.status_code == 422
    assert "must be 'character', 'film', or 'starship'" in resp.json()["detail"]

async def test_cast_vote_not_found(async_client: AsyncClient):
    """Test casting a vote for a non-existent resource."""
    payload = {
        "resource_type": "character",
        "resource_id": 9999 # Doesn't exist
    }
    resp = await async_client.post("/api/votes", json=payload)
    assert resp.status_code == 404
    assert "Character with ID 9999 not found" in resp.json()["detail"]

async def test_get_vote_count(async_client: AsyncClient, db_session: AsyncSession):
    """Test retrieving vote counts."""
    char = await seed_data(db_session)
    
    # Cast a vote
    payload = {"resource_type": "character", "resource_id": char.id}
    await async_client.post("/api/votes", json=payload)
    await async_client.post("/api/votes", json=payload)
    
    # Get count
    resp = await async_client.get(f"/api/votes/character/{char.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["resource_type"] == "character"
    assert data["resource_id"] == char.id
    assert data["count"] == 2
    
    # Invalid type
    resp_invalid = await async_client.get(f"/api/votes/planet/{char.id}")
    assert resp_invalid.status_code == 422
