from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime


class VoteCreate(BaseModel):
    """Empty on purpose — the resource being voted on is identified entirely
    by the `resource_type`/`resource_id` path params on POST /votes/{type}/{id},
    so no request body fields are needed."""
    pass


class VoteResponse(BaseModel):
    id: int = Field(..., description="Internal id of this vote record")
    resource_type: str = Field(..., description="Type of resource voted on: 'character', 'film', or 'starship'")
    resource_id: int = Field(..., description="Local (not SWAPI) id of the voted-on resource")
    created_at: datetime = Field(..., description="Timestamp the vote was cast, in UTC")

    model_config = ConfigDict(from_attributes=True)


class VoteCount(BaseModel):
    resource_type: str = Field(..., description="Type of resource: 'character', 'film', or 'starship'")
    resource_id: int = Field(..., description="Local id of the resource")
    vote_count: int = Field(..., description="Total number of votes this resource has received")


class CharacterBase(BaseModel):
    name: str = Field(..., description="Character's full name, as returned by SWAPI")
    height: Optional[str] = Field(None, description="Height in centimeters (kept as string to match SWAPI, which uses 'unknown' for some records)")
    mass: Optional[str] = Field(None, description="Mass in kilograms (string, same reasoning as height)")
    birth_year: Optional[str] = Field(None, description="Birth year in SWAPI's BBY/ABY notation")
    swapi_id: int = Field(..., description="Numeric id of this resource on SWAPI, extracted from its URL")
    swapi_url: str = Field(..., description="Canonical SWAPI URL this record was synced from")


class CharacterResponse(CharacterBase):
    id: int = Field(..., description="Local database id — use this for votes and lookups against this API")

    model_config = ConfigDict(from_attributes=True)


class FilmBase(BaseModel):
    title: str = Field(..., description="Film title")
    episode_id: int = Field(..., description="Saga episode number")
    release_date: Optional[str] = Field(None, description="ISO release date, e.g. '1977-05-25'")
    director: Optional[str] = Field(None, description="Film director")
    swapi_id: int = Field(..., description="Numeric id of this resource on SWAPI, extracted from its URL")
    swapi_url: str = Field(..., description="Canonical SWAPI URL this record was synced from")


class FilmResponse(FilmBase):
    id: int = Field(..., description="Local database id — use this for votes and lookups against this API")

    model_config = ConfigDict(from_attributes=True)


class StarshipBase(BaseModel):
    name: str = Field(..., description="Starship name")
    model: Optional[str] = Field(None, description="Manufacturer's model designation")
    manufacturer: Optional[str] = Field(None, description="Manufacturer name")
    swapi_id: int = Field(..., description="Numeric id of this resource on SWAPI, extracted from its URL")
    swapi_url: str = Field(..., description="Canonical SWAPI URL this record was synced from")


class StarshipResponse(StarshipBase):
    id: int = Field(..., description="Local database id — use this for votes and lookups against this API")

    model_config = ConfigDict(from_attributes=True)


class PaginatedCharacters(BaseModel):
    count: int = Field(..., description="Total number of characters in the database (not just this page)")
    results: List[CharacterResponse]


class PaginatedFilms(BaseModel):
    count: int = Field(..., description="Total number of films in the database (not just this page)")
    results: List[FilmResponse]


class PaginatedStarships(BaseModel):
    count: int = Field(..., description="Total number of starships in the database (not just this page)")
    results: List[StarshipResponse]


class SyncResult(BaseModel):
    resource_type: str = Field(..., description="Which resource type this sync run covered")
    synced: int = Field(..., description="Total records fetched from SWAPI for this run")
    created: int = Field(..., description="Records that were new and got inserted")
    updated: int = Field(..., description="Records that already existed and got updated in place")
