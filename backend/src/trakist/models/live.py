"""LiveSession, LiveComment, Reservation, Transaction — module de reconciliation
live (cahier des charges §3.4, §4, §5.4)."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from trakist.db import Base


class StatutLive(str, enum.Enum):
    EN_COURS = "en_cours"
    TERMINEE = "terminee"


class StatutComment(str, enum.Enum):
    NOUVEAU = "nouveau"
    EN_FILE = "en_file"
    RESERVE = "reserve"
    EXPIRE = "expire"
    CONFIRME = "confirme"


class StatutReservation(str, enum.Enum):
    EN_ATTENTE = "en_attente"
    PAIEMENT_DEMANDE = "paiement_demande"
    CONFIRMEE = "confirmee"
    EXPIREE = "expiree"
    LIBEREE = "liberee"


class RailPaiement(str, enum.Enum):
    MOMO = "momo"
    ORANGE_MONEY = "orange_money"


class StatutTransaction(str, enum.Enum):
    INITIEE = "initiee"
    CONFIRMEE = "confirmee"
    ECHOUEE = "echouee"
    EXPIREE = "expiree"


class LiveSession(Base):
    __tablename__ = "live_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id"))
    channel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("channels.id"))
    statut: Mapped[StatutLive] = mapped_column(Enum(StatutLive), default=StatutLive.EN_COURS)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    comments: Mapped[list["LiveComment"]] = relationship(back_populates="live_session")


class LiveComment(Base):
    __tablename__ = "live_comments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    live_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("live_sessions.id"))
    auteur: Mapped[str] = mapped_column(String(255))
    texte: Mapped[str] = mapped_column(Text)
    horodatage: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    statut: Mapped[StatutComment] = mapped_column(Enum(StatutComment), default=StatutComment.NOUVEAU)

    live_session: Mapped["LiveSession"] = relationship(back_populates="comments")
    reservation: Mapped["Reservation | None"] = relationship(back_populates="live_comment", uselist=False)


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    live_comment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("live_comments.id"))
    article_ref: Mapped[str] = mapped_column(String(255))
    statut: Mapped[StatutReservation] = mapped_column(
        Enum(StatutReservation), default=StatutReservation.EN_ATTENTE
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    live_comment: Mapped["LiveComment"] = relationship(back_populates="reservation")
    transaction: Mapped["Transaction | None"] = relationship(back_populates="reservation", uselist=False)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    reservation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reservations.id"))
    rail: Mapped[RailPaiement] = mapped_column(Enum(RailPaiement))
    montant: Mapped[float] = mapped_column(Numeric(12, 2))
    devise: Mapped[str] = mapped_column(String(3), default="XOF")
    statut: Mapped[StatutTransaction] = mapped_column(Enum(StatutTransaction), default=StatutTransaction.INITIEE)
    reference_externe: Mapped[str | None] = mapped_column(String(255), nullable=True)
    webhook_recu_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    reservation: Mapped["Reservation"] = relationship(back_populates="transaction")
