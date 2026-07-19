import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Character, Film, Starship

pytestmark = pytest.mark.asyncio

async def seed_data(db_session: AsyncSession):
    """Helper to inject some test data directly into the DB."""
    film1 = Film(swapi_id=1, swapi_url="https://swapi.dev/api/films/1/", title="A New Hope", episode_id=4)
    film2 = Film(swapi_id=2, swapi_url="https://swapi.dev/api/films/2/", title="The Empire Strikes Back", episode_id=5)
    
    char1 = Character(swapi_id=1, swapi_url="https://swapi.dev/api/people/1/", name="Luke Skywalker")
    char2 = Character(swapi_id=4, swapi_url="https://swapi.dev/api/people/4/", name="Darth Vader")
    
    ship1 = Starship(swapi_id=12, swapi_url="https://swapi.dev/api/starships/12/", name="X-wing")
    
    db_session.add_all([film1, film2, char1, char2, ship1])
    await db_session.commit()

async def test_pagination(async_client: AsyncClient, db_session: AsyncSession):
    """Test pagination works across endpoints."""
    await seed_data(db_session)
    
    # Test characters pagination
    resp = await async_client.get("/api/characters?skip=0&limit=1")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    
    resp2 = await async_client.get("/api/characters?skip=1&limit=1")
    assert resp2.status_code == 200
    assert len(resp2.json()) == 1
    assert resp.json()[0]["id"] != resp2.json()[0]["id"]

async def test_search_case_insensitive(async_client: AsyncClient, db_session: AsyncSession):
    """Test case-insensitive partial match search."""
    await seed_data(db_session)
    
    # Test lowercase search matches uppercase data
    resp = await async_client.get("/api/characters/search?name=luke")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Luke Skywalker"
    
    # Test partial match
    resp2 = await async_client.get("/api/films/search?title=empire")
    assert resp2.status_code == 200
    assert len(resp2.json()) == 1
    assert resp2.json()[0]["title"] == "The Empire Strikes Back"
    
    # Test no match
    resp3 = await async_client.get("/api/starships/search?name=falcon")
    assert resp3.status_code == 200
    assert len(resp3.json()) == 0
