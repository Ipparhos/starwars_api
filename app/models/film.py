from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.associations import character_films

class Film(Base):
    __tablename__ = "films"

    id = Column(Integer, primary_key=True, index=True)
    swapi_id = Column(Integer, unique=True, index=True, nullable=False)
    swapi_url = Column(String, unique=True, nullable=False)
    
    title = Column(String, index=True, nullable=False)
    episode_id = Column(Integer, nullable=False)
    release_date = Column(String, nullable=True)
    director = Column(String, nullable=True)
    
    characters = relationship("Character", secondary=character_films, back_populates="films")
