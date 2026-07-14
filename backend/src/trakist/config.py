from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"
    database_url: str = "postgresql+psycopg://trakist:trakist@localhost:5432/trakist"
    redis_url: str = "redis://localhost:6379/0"
    whatsapp_api_token: str = ""
    whatsapp_phone_number_id: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
