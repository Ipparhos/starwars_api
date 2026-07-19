from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn


class Settings(BaseSettings):
    PROJECT_NAME: str = "Star Wars API"
    VERSION: str = "1.0.0"
    
    # SWAPI configuration
    SWAPI_BASE_URL: str = "https://swapi.dev/api"
    SWAPI_TIMEOUT_SECONDS: int = 10
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/starwars"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
