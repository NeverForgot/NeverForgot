from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"
    database_url: str = "postgresql+psycopg://trakist:trakist@localhost:5432/trakist"
    redis_url: str = "redis://localhost:6379/0"
    whatsapp_api_token: str = ""
    whatsapp_phone_number_id: str = ""
    anthropic_api_key: str = ""
    # Haiku 4.5 par defaut : volume eleve, prompts courts, tache de
    # classification peu complexe (§5.3). A remonter vers Sonnet si le taux
    # de pertinence mesure en cohorte pilote (§2.2) le justifie.
    classification_model: str = "claude-haiku-4-5"


@lru_cache
def get_settings() -> Settings:
    return Settings()
