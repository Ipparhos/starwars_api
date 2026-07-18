from sqlalchemy import Column, Integer, ForeignKey, Table
from app.database import Base

character_films = Table(
    "character_films",
    Base.metadata,
    Column("character_id", Integer, ForeignKey("characters.id"), primary_key=True),
    Column("film_id", Integer, ForeignKey("films.id"), primary_key=True),
)

character_starships = Table(
    "character_starships",
    Base.metadata,
    Column("character_id", Integer, ForeignKey("characters.id"), primary_key=True),
    Column("starship_id", Integer, ForeignKey("starships.id"), primary_key=True),
)
