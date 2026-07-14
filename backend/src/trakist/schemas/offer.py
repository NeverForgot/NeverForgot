import uuid

from pydantic import BaseModel, ConfigDict


class OfferCreate(BaseModel):
    libelle: str
    mots_cles: list[str] = []
    zone_geo_cible: str | None = None


class OfferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    libelle: str
    mots_cles: list[str]
    zone_geo_cible: str | None
