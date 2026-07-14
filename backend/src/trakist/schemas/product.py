import uuid

from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    reference: str
    libelle: str
    prix: float
    devise: str = "XOF"


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    reference: str
    libelle: str
    prix: float
    devise: str
    actif: bool
