import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from trakist.models.live import StatutComment, StatutLive, StatutReservation, StatutTransaction


class LiveSessionCreate(BaseModel):
    business_id: uuid.UUID
    channel_id: uuid.UUID


class LiveSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    channel_id: uuid.UUID
    statut: StatutLive
    started_at: datetime
    ended_at: datetime | None


class LiveCommentCreate(BaseModel):
    auteur: str
    texte: str
    article_ref: str


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rail: str
    montant: float
    devise: str
    statut: StatutTransaction
    reference_externe: str | None


class ReservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    article_ref: str
    statut: StatutReservation
    expires_at: datetime | None
    transaction: TransactionOut | None


class LiveCommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    auteur: str
    texte: str
    horodatage: datetime
    statut: StatutComment
    reservation: ReservationOut | None


class PaymentWebhookPayload(BaseModel):
    reference_externe: str
