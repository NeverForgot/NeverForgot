import uuid

from pydantic import BaseModel, ConfigDict

from trakist.models.signal import LangueDetectee, StatutSignal


class SignalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    texte_source: str
    url_source: str | None
    langue_detectee: LangueDetectee
    score_pertinence: float
    score_confiance_linguistique: float
    statut: StatutSignal


class SignalFeedback(BaseModel):
    pertinent: bool


class MessageIngestCreate(BaseModel):
    texte: str
    auteur: str | None = None
    url_source: str | None = None


class WhatsAppInboundMessage(BaseModel):
    texte: str
