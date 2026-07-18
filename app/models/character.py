from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.associations import character_films, character_starships

class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    swapi_id = Column(Integer, unique=True, index=True, nullable=False)
    swapi_url = Column(String, unique=True, nullable=False)
    
    name = Column(String, index=True, nullable=False)
    height = Column(String, nullable=True)
    mass = Column(String, nullable=True)
    birth_year = Column(String, nullable=True)
    
    films = relationship("Film", secondary=character_films, back_populates="characters")
    starships = relationship("Starship", secondary=character_starships, back_populates="pilots")
