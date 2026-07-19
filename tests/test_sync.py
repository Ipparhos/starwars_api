import pytest
import respx
from httpx import AsyncClient, Response

pytestmark = pytest.mark.asyncio

import re

@respx.mock
async def test_sync_success(async_client: AsyncClient):
    """Test successful synchronization with SWAPI using mocked endpoints."""
    
    # Mock Films
    respx.get(re.compile(r"https://swapi\.dev/api/films.*")).mock(return_value=Response(200, json={
        "next": None,
        "results": [
            {
                "title": "A New Hope",
                "episode_id": 4,
                "url": "https://swapi.dev/api/films/1/"
            }
        ]
    }))
    
    # Mock Starships
    respx.get(re.compile(r"https://swapi\.dev/api/starships.*")).mock(return_value=Response(200, json={
        "next": None,
        "results": [
            {
                "name": "X-wing",
                "url": "https://swapi.dev/api/starships/12/"
            }
        ]
    }))
    
    # Mock Characters
    respx.get(re.compile(r"https://swapi\.dev/api/people.*")).mock(return_value=Response(200, json={
        "next": None,
        "results": [
            {
                "name": "Luke Skywalker",
                "url": "https://swapi.dev/api/people/1/",
                "films": ["https://swapi.dev/api/films/1/"],
                "starships": ["https://swapi.dev/api/starships/12/"]
            }
        ]
    }))

    response = await async_client.post("/api/sync")
    assert response.status_code == 202
    
    data = response.json()
    assert data["message"] == "Sync completed successfully"
    assert len(data["details"]) == 3
    
    # Verify the results in the response
    assert data["details"][0]["resource_type"] == "film"
    assert data["details"][0]["synced"] == 1
    assert data["details"][2]["resource_type"] == "character"
    assert data["details"][2]["synced"] == 1

@respx.mock
async def test_sync_swapi_down(async_client: AsyncClient):
    """Test sync gracefully handles SWAPI being down and returns 503."""
    
    # Mock a 500 internal server error from SWAPI
    respx.get(re.compile(r"https://swapi\.dev/api/.*")).mock(return_value=Response(500))
    
    response = await async_client.post("/api/sync")
    
    # Our global exception handler maps SWAPIUnavailableError to 503
    assert response.status_code == 503
    assert "detail" in response.json()

@respx.mock
async def test_sync_idempotency_and_individual_endpoints(async_client: AsyncClient):
    """Test individual sync endpoints and idempotency (updating existing records)."""
    
    # Mock Films
    film_route = respx.get(re.compile(r"https://swapi\.dev/api/films.*")).mock(return_value=Response(200, json={
        "next": None,
        "results": [
            {
                "title": "A New Hope",
                "episode_id": 4,
                "url": "https://swapi.dev/api/films/1/"
            }
        ]
    }))
    
    # Mock Starships
    ship_route = respx.get(re.compile(r"https://swapi\.dev/api/starships.*")).mock(return_value=Response(200, json={
        "next": None,
        "results": [
            {
                "name": "X-wing",
                "url": "https://swapi.dev/api/starships/12/"
            }
        ]
    }))
    
    # Mock Characters
    char_route = respx.get(re.compile(r"https://swapi\.dev/api/people.*")).mock(return_value=Response(200, json={
        "next": None,
        "results": [
            {
                "name": "Luke Skywalker",
                "mass": "77",
                "url": "https://swapi.dev/api/people/1/",
                "films": ["https://swapi.dev/api/films/1/"],
                "starships": ["https://swapi.dev/api/starships/12/"]
            }
        ]
    }))

    # 1. Sync individually (creates new records)
    resp_f = await async_client.post("/api/sync/films")
    assert resp_f.status_code == 202, resp_f.text
    
    resp_s = await async_client.post("/api/sync/starships")
    assert resp_s.status_code == 202
    
    resp_c = await async_client.post("/api/sync/characters")
    assert resp_c.status_code == 202

    # 2. Update mocks to simulate changed data from SWAPI
    char_route.mock(return_value=Response(200, json={
        "next": None,
        "results": [
            {
                "name": "Luke Skywalker",
                "mass": "80", # Changed mass
                "url": "https://swapi.dev/api/people/1/",
                "films": ["https://swapi.dev/api/films/1/"],
                "starships": ["https://swapi.dev/api/starships/12/"]
            }
        ]
    }))
    
    film_route.mock(return_value=Response(200, json={
        "next": None,
        "results": [
            {
                "title": "A New Hope - Special Edition", # Changed title
                "episode_id": 4,
                "url": "https://swapi.dev/api/films/1/"
            }
        ]
    }))
    
    ship_route.mock(return_value=Response(200, json={
        "next": None,
        "results": [
            {
                "name": "X-wing Fighter", # Changed name
                "url": "https://swapi.dev/api/starships/12/"
            }
        ]
    }))

    # 3. Sync individually again (triggers update paths)
    await async_client.post("/api/sync/films")
    await async_client.post("/api/sync/starships")
    await async_client.post("/api/sync/characters")
    
    # 4. Verify no duplicates and data is updated
    chars = await async_client.get("/api/characters")
    assert len(chars.json()) == 1
    assert chars.json()[0]["mass"] == "80"
    
    films = await async_client.get("/api/films")
    assert len(films.json()) == 1
    assert films.json()[0]["title"] == "A New Hope - Special Edition"
    
    ships = await async_client.get("/api/starships")
    assert len(ships.json()) == 1
    assert ships.json()[0]["name"] == "X-wing Fighter"
