from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_ENV: str = "development"
    SECRET_KEY: str = "crewwatch-super-secret-jwt-key-change-in-prod-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    NASA_API_KEY: str = ""
    DATABASE_URL: str = ""
    DIRECT_URL: str = ""
    REDIS_URL: str = ""
    SIMULATOR_TICK_SECONDS: int = 5
    DEMO_MODE: bool = False

    class Config:
        env_file = ".env"
        extra = "allow"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
