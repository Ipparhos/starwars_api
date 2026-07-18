from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.associations import character_starships

class Starship(Base):
    __tablename__ = "starships"

    id = Column(Integer, primary_key=True, index=True)
    swapi_id = Column(Integer, unique=True, index=True, nullable=False)
    swapi_url = Column(String, unique=True, nullable=False)
    
    name = Column(String, index=True, nullable=False)
    model = Column(String, nullable=True)
    manufacturer = Column(String, nullable=True)
    
    pilots = relationship("Character", secondary=character_starships, back_populates="starships")
