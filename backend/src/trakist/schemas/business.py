import uuid

from pydantic import BaseModel, ConfigDict

from trakist.models.business import FrequenceRapport


class BusinessCreate(BaseModel):
    nom: str
    secteur: str
    ville: str
    country_code: str
    numero_paiement_momo: str
    numero_whatsapp: str
    frequence_rapport: FrequenceRapport = FrequenceRapport.DAILY
    seuil_pertinence: float = 0.5
    fuseau_horaire: str = "Africa/Porto-Novo"
    langue_communication: str = "fr"


class BusinessOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nom: str
    secteur: str
    ville: str
    country_code: str
    numero_whatsapp: str
    frequence_rapport: FrequenceRapport
    seuil_pertinence: float
