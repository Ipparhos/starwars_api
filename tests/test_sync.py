import pytest
import respx
from httpx import AsyncClient, Response

pytestmark = pytest.mark.asyncio

import re

from app.routers.sync import _run_sync_task

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
    assert response.json()["message"] == "Sync started in the background"
    task_id = response.json()["task_id"]
    
    # Check status before running task (unknown since we are testing manually)
    status_resp = await async_client.get(f"/api/sync/status/{task_id}")
    assert status_resp.status_code == 200
    
    # Manually run the background task logic to test it
    await _run_sync_task(task_id, "sync_all")
    
    # Check status after running task
    status_resp = await async_client.get(f"/api/sync/status/{task_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "completed"
    
    # Verify the results in the database
    chars = await async_client.get("/api/characters")
    data = chars.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "Luke Skywalker"

@respx.mock
async def test_sync_swapi_down(async_client: AsyncClient):
    """Test sync gracefully handles SWAPI being down and returns 503."""
    
    # Mock a 500 internal server error from SWAPI
    respx.get(re.compile(r"https://swapi\.dev/api/.*")).mock(return_value=Response(500))
    
    response = await async_client.post("/api/sync")
    
    # Since sync is now a background task, it always returns 202 immediately.
    assert response.status_code == 202
    
    # Manually run the background logic to ensure it handles the SWAPI failure gracefully
    # The exception should be caught and logged by _run_sync_task, so this won't crash
    task_id = response.json()["task_id"]
    await _run_sync_task(task_id, "sync_all")
    
    # Check status
    status_resp = await async_client.get(f"/api/sync/status/{task_id}")
    assert status_resp.json()["status"] == "failed"

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

    # 1. Sync individually via API (triggers background tasks)
    resp_f = await async_client.post("/api/sync/films")
    assert resp_f.status_code == 202
    
    resp_s = await async_client.post("/api/sync/starships")
    assert resp_s.status_code == 202
    
    resp_c = await async_client.post("/api/sync/characters")
    assert resp_c.status_code == 202
    
    # Await background logic manually for test determinism
    await _run_sync_task(resp_f.json()["task_id"], "sync_films")
    await _run_sync_task(resp_s.json()["task_id"], "sync_starships")
    await _run_sync_task(resp_c.json()["task_id"], "sync_characters")

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

    # 3. Sync individually again via API
    r_f = await async_client.post("/api/sync/films")
    r_s = await async_client.post("/api/sync/starships")
    r_c = await async_client.post("/api/sync/characters")
    
    # Await background logic manually to perform the updates
    await _run_sync_task(r_f.json()["task_id"], "sync_films")
    await _run_sync_task(r_s.json()["task_id"], "sync_starships")
    await _run_sync_task(r_c.json()["task_id"], "sync_characters")
    
    # 4. Verify no duplicates and data is updated
    chars = await async_client.get("/api/characters")
    assert len(chars.json()["data"]) == 1
    assert chars.json()["data"][0]["mass"] == "80"
    
    films = await async_client.get("/api/films")
    assert len(films.json()["data"]) == 1
    assert films.json()["data"][0]["title"] == "A New Hope - Special Edition"
    
    ships = await async_client.get("/api/starships")
    assert len(ships.json()["data"]) == 1
    assert ships.json()["data"][0]["name"] == "X-wing Fighter"
