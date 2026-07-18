import re
from typing import Callable, Awaitable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Character, Film, Starship
from app.services.swapi_client import SWAPIClient

_TRAILING_ID_RE = re.compile(r"/(\d+)/?$")


def extract_swapi_id(url: str) -> int:
    """Pull the numeric resource id out of a SWAPI resource URL.

    e.g. "https://swapi.dev/api/people/1/" -> 1
    """
    match = _TRAILING_ID_RE.search(url)
    if not match:
        raise ValueError(f"Could not extract a SWAPI id from URL: {url!r}")
    return int(match.group(1))


class SyncService:
    """Fetches resources from SWAPI and upserts them into the local database.

    Films and starships are synced first so that when characters are synced,
    their `films` / `starships` relationships can be resolved from the SWAPI
    URLs embedded in the character payload.
    """

    def __init__(self, db: AsyncSession, client: SWAPIClient | None = None):
        self.db = db
        self.client = client or SWAPIClient()

    async def _fetch_all_pages(
        self, fetch_page: Callable[..., Awaitable[dict]]
    ) -> list[dict]:
        results: list[dict] = []
        page = 1
        while True:
            data = await fetch_page(page=page)
            results.extend(data.get("results", []))
            if not data.get("next"):
                break
            page += 1
        return results

    async def sync_films(self) -> dict:
        raw_films = await self._fetch_all_pages(self.client.get_films)
        created, updated = 0, 0

        for raw in raw_films:
            swapi_id = extract_swapi_id(raw["url"])
            existing = await self.db.scalar(
                select(Film).where(Film.swapi_id == swapi_id)
            )
            if existing:
                existing.title = raw["title"]
                existing.episode_id = raw["episode_id"]
                existing.release_date = raw.get("release_date")
                existing.director = raw.get("director")
                updated += 1
            else:
                self.db.add(
                    Film(
                        swapi_id=swapi_id,
                        swapi_url=raw["url"],
                        title=raw["title"],
                        episode_id=raw["episode_id"],
                        release_date=raw.get("release_date"),
                        director=raw.get("director"),
                    )
                )
                created += 1

        await self.db.commit()
        return {
            "resource_type": "film",
            "synced": len(raw_films),
            "created": created,
            "updated": updated,
        }

    async def sync_starships(self) -> dict:
        raw_starships = await self._fetch_all_pages(self.client.get_starships)
        created, updated = 0, 0

        for raw in raw_starships:
            swapi_id = extract_swapi_id(raw["url"])
            existing = await self.db.scalar(
                select(Starship).where(Starship.swapi_id == swapi_id)
            )
            if existing:
                existing.name = raw["name"]
                existing.model = raw.get("model")
                existing.manufacturer = raw.get("manufacturer")
                updated += 1
            else:
                self.db.add(
                    Starship(
                        swapi_id=swapi_id,
                        swapi_url=raw["url"],
                        name=raw["name"],
                        model=raw.get("model"),
                        manufacturer=raw.get("manufacturer"),
                    )
                )
                created += 1

        await self.db.commit()
        return {
            "resource_type": "starship",
            "synced": len(raw_starships),
            "created": created,
            "updated": updated,
        }

    async def sync_characters(self) -> dict:
        raw_people = await self._fetch_all_pages(self.client.get_characters)
        created, updated = 0, 0

        for raw in raw_people:
            swapi_id = extract_swapi_id(raw["url"])

            film_ids = [extract_swapi_id(u) for u in raw.get("films", [])]
            starship_ids = [extract_swapi_id(u) for u in raw.get("starships", [])]

            films = (
                (await self.db.scalars(select(Film).where(Film.swapi_id.in_(film_ids))))
                .all()
                if film_ids
                else []
            )
            starships = (
                (
                    await self.db.scalars(
                        select(Starship).where(Starship.swapi_id.in_(starship_ids))
                    )
                ).all()
                if starship_ids
                else []
            )

            existing = await self.db.scalar(
                select(Character)
                .options(
                    selectinload(Character.films),
                    selectinload(Character.starships),
                )
                .where(Character.swapi_id == swapi_id)
            )

            if existing:
                existing.name = raw["name"]
                existing.height = raw.get("height")
                existing.mass = raw.get("mass")
                existing.birth_year = raw.get("birth_year")
                existing.films = list(films)
                existing.starships = list(starships)
                updated += 1
            else:
                self.db.add(
                    Character(
                        swapi_id=swapi_id,
                        swapi_url=raw["url"],
                        name=raw["name"],
                        height=raw.get("height"),
                        mass=raw.get("mass"),
                        birth_year=raw.get("birth_year"),
                        films=list(films),
                        starships=list(starships),
                    )
                )
                created += 1

        await self.db.commit()
        return {
            "resource_type": "character",
            "synced": len(raw_people),
            "created": created,
            "updated": updated,
        }

    async def sync_all(self) -> list[dict]:
        # Order matters: films/starships must exist before character
        # relationships can be resolved against them.
        film_result = await self.sync_films()
        starship_result = await self.sync_starships()
        character_result = await self.sync_characters()
        return [film_result, starship_result, character_result]
