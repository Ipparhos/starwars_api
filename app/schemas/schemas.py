from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime

class VoteCreate(BaseModel):
    """Payload to cast a vote for a specific resource."""
    resource_type: str = Field(..., description="The type of resource: 'character', 'film', or 'starship'.")
    resource_id: int = Field(..., description="The internal database ID of the resource.")

class VoteResponse(BaseModel):
    """Response model for a recorded vote."""
    id: int = Field(..., description="The unique ID of the vote.")
    resource_type: str = Field(..., description="The type of resource voted for.")
    resource_id: int = Field(..., description="The internal database ID of the resource voted for.")
    created_at: datetime = Field(..., description="When the vote was cast.")
    
    model_config = ConfigDict(from_attributes=True)

class CharacterBase(BaseModel):
    name: str = Field(..., description="The name of the character.")
    height: Optional[str] = Field(None, description="The height of the character in cm.")
    mass: Optional[str] = Field(None, description="The mass of the character in kg.")
    birth_year: Optional[str] = Field(None, description="The birth year of the character (e.g. 19BBY).")
    swapi_id: int = Field(..., description="The original ID of the character from SWAPI.")
    swapi_url: str = Field(..., description="The original URL of the character from SWAPI.")

class CharacterResponse(CharacterBase):
    """Response model for a Star Wars character."""
    id: int = Field(..., description="The internal database ID.")
    
    model_config = ConfigDict(from_attributes=True)

class FilmBase(BaseModel):
    title: str = Field(..., description="The title of the film.")
    episode_id: int = Field(..., description="The episode number of the film.")
    release_date: Optional[str] = Field(None, description="The release date of the film.")
    director: Optional[str] = Field(None, description="The director of the film.")
    swapi_id: int = Field(..., description="The original ID of the film from SWAPI.")
    swapi_url: str = Field(..., description="The original URL of the film from SWAPI.")

class FilmResponse(FilmBase):
    """Response model for a Star Wars film."""
    id: int = Field(..., description="The internal database ID.")
    
    model_config = ConfigDict(from_attributes=True)

class StarshipBase(BaseModel):
    name: str = Field(..., description="The name of the starship.")
    model: Optional[str] = Field(None, description="The model of the starship.")
    manufacturer: Optional[str] = Field(None, description="The manufacturer of the starship.")
    swapi_id: int = Field(..., description="The original ID of the starship from SWAPI.")
    swapi_url: str = Field(..., description="The original URL of the starship from SWAPI.")

class StarshipResponse(StarshipBase):
    """Response model for a Star Wars starship."""
    id: int = Field(..., description="The internal database ID.")
    
    model_config = ConfigDict(from_attributes=True)
