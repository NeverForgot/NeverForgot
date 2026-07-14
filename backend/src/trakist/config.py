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
    # Ordonnanceur interne (scheduler.py) : declenche automatiquement la
    # generation des rapports dus et l'expiration des reservations live.
    # A desactiver (ex. dans les tests d'integration ou en execution
    # multi-instance sans ordonnanceur externe partage) via
    # SCHEDULER_ENABLED=false.
    scheduler_enabled: bool = True
    scheduler_intervalle_rapports_minutes: int = 15
    # Frequent par defaut : la fenetre d'expiration d'une reservation
    # (DEFAULT_FENETRE_EXPIRATION, live_service.py) est de 5 minutes.
    scheduler_intervalle_reservations_minutes: int = 1
    # Verification provisoire des webhooks entrants (paiement MoMo/Orange,
    # feedback WhatsApp) par secret partage (`api/security.py`), en
    # attendant les signatures reelles par fournisseur une fois les
    # identifiants par pays configures (§5.2). Vide par defaut = tous les
    # webhooks rejetes (fail closed) : positionner explicitement pour
    # activer, y compris en developpement local.
    webhook_shared_secret: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
