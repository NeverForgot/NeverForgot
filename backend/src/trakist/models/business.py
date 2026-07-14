"""Business, Offer, Channel (cahier des charges §4)."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from trakist.db import Base


class FrequenceRapport(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"


class ChannelType(str, enum.Enum):
    FACEBOOK_GROUP = "facebook_group"
    WHATSAPP_GROUP = "whatsapp_group"
    TIKTOK_OWN = "tiktok_own"
    GOOGLE_SEARCH = "google_search"


class StatutConnexion(str, enum.Enum):
    CONNECTE = "connecte"
    DECONNECTE = "deconnecte"
    ERREUR = "erreur"


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nom: Mapped[str] = mapped_column(String(255))
    secteur: Mapped[str] = mapped_column(String(255))  # libre, non limite a une liste fermee
    ville: Mapped[str] = mapped_column(String(255))
    country_code: Mapped[str] = mapped_column(ForeignKey("countries.code"))
    numero_paiement_momo: Mapped[str] = mapped_column(String(32))
    numero_whatsapp: Mapped[str] = mapped_column(String(32))
    frequence_rapport: Mapped[FrequenceRapport] = mapped_column(
        Enum(FrequenceRapport), default=FrequenceRapport.DAILY
    )
    # Seuil de pertinence configurable pour eviter la fatigue du rapport (§3.2).
    seuil_pertinence: Mapped[float] = mapped_column(Float, default=0.5)
    fuseau_horaire: Mapped[str] = mapped_column(String(64), default="Africa/Porto-Novo")
    langue_communication: Mapped[str] = mapped_column(String(8), default="fr")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    country: Mapped["Country"] = relationship(back_populates="businesses")
    offers: Mapped[list["Offer"]] = relationship(back_populates="business")
    channels: Mapped[list["Channel"]] = relationship(back_populates="business")
    products: Mapped[list["Product"]] = relationship(back_populates="business")


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id"))
    libelle: Mapped[str] = mapped_column(String(255))
    # JSON sous SQLite (tests) : ARRAY natif est specifique Postgres.
    mots_cles: Mapped[list[str]] = mapped_column(ARRAY(String).with_variant(JSON(), "sqlite"), default=list)
    zone_geo_cible: Mapped[str | None] = mapped_column(String(255), nullable=True)

    business: Mapped["Business"] = relationship(back_populates="offers")


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    type: Mapped[ChannelType] = mapped_column(Enum(ChannelType))
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id"))
    identifiant_externe: Mapped[str] = mapped_column(String(255))
    statut_connexion: Mapped[StatutConnexion] = mapped_column(
        Enum(StatutConnexion), default=StatutConnexion.DECONNECTE
    )

    business: Mapped["Business"] = relationship(back_populates="channels")
