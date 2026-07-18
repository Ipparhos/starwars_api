from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class VoteCreate(BaseModel):
    pass

class VoteResponse(BaseModel):
    id: int
    resource_type: str
    resource_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class CharacterBase(BaseModel):
    name: str
    height: Optional[str] = None
    mass: Optional[str] = None
    birth_year: Optional[str] = None
    swapi_id: int
    swapi_url: str

class CharacterResponse(CharacterBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class FilmBase(BaseModel):
    title: str
    episode_id: int
    release_date: Optional[str] = None
    director: Optional[str] = None
    swapi_id: int
    swapi_url: str

class FilmResponse(FilmBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class StarshipBase(BaseModel):
    name: str
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    swapi_id: int
    swapi_url: str

class StarshipResponse(StarshipBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)
