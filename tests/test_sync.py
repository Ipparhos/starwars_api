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
