"""Country et GlossaryEntry : entites de premier plan (cahier des charges §4).

Elles alimentent dynamiquement le prompt de classification (§5.5) et
permettent de partager un seul moteur entre les 3 pays sans dupliquer le code.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from trakist.db import Base


class GlossaryCategorie(str, enum.Enum):
    INTENTION_ACHAT = "intention_achat"
    QUESTION = "question"
    NEGOCIATION = "negociation"
    AUTRE = "autre"


class GlossarySource(str, enum.Enum):
    CURATION_MANUELLE = "curation_manuelle"
    REMONTEE_PILOTE = "remontee_pilote"


class Country(Base):
    """Profil marche : un pays = une configuration, jamais un fork du produit."""

    __tablename__ = "countries"

    code: Mapped[str] = mapped_column(String(2), primary_key=True)  # BJ | CI | SN
    langue_dominante: Mapped[str] = mapped_column(String(8), default="fr")
    # JSON sous SQLite (tests) : ARRAY natif est specifique Postgres.
    rails_paiement_disponibles: Mapped[list[str]] = mapped_column(
        ARRAY(String).with_variant(JSON(), "sqlite"), default=list
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    glossary_entries: Mapped[list["GlossaryEntry"]] = relationship(back_populates="country")
    businesses: Mapped[list["Business"]] = relationship(back_populates="country")


class GlossaryEntry(Base):
    """Expression d'argot local. country_code nul = socle partage entre les 3 pays."""

    __tablename__ = "glossary_entries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    country_code: Mapped[str | None] = mapped_column(ForeignKey("countries.code"), nullable=True)
    expression: Mapped[str] = mapped_column(String(255))
    signification: Mapped[str] = mapped_column(Text)
    exemple_usage: Mapped[str | None] = mapped_column(Text, nullable=True)
    categorie: Mapped[GlossaryCategorie] = mapped_column(Enum(GlossaryCategorie))
    source: Mapped[GlossarySource] = mapped_column(Enum(GlossarySource))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    country: Mapped["Country | None"] = relationship(back_populates="glossary_entries")
