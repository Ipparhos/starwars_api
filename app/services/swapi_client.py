import httpx
from tenacity import retry, wait_exponential, stop_after_attempt
from app.config import settings

class SWAPIUnavailableError(Exception):
    """Custom exception raised when SWAPI is unreachable or returns a 500 error."""
    pass

class SWAPIClient:
    def __init__(self):
        self.base_url = settings.SWAPI_BASE_URL
        self.timeout = settings.SWAPI_TIMEOUT_SECONDS

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True
    )
    async def _get(self, endpoint: str, params: dict = None) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(f"{self.base_url}/{endpoint}", params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500:
                    raise SWAPIUnavailableError(f"SWAPI is currently unavailable: {e}")
                raise
            except httpx.RequestError as e:
                raise SWAPIUnavailableError(f"Failed to connect to SWAPI: {e}")

    async def get_characters(self, page: int = 1) -> dict:
        return await self._get("people", params={"page": page})

    async def get_films(self, page: int = 1) -> dict:
        return await self._get("films", params={"page": page})

    async def get_starships(self, page: int = 1) -> dict:
        return await self._get("starships", params={"page": page})
