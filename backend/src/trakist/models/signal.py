"""Signal (prospect detecte) et Report (cahier des charges §4)."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from trakist.db import Base


class LangueDetectee(str, enum.Enum):
    FR = "fr"
    EN = "en"
    MIXTE = "mixte"


class StatutSignal(str, enum.Enum):
    NOUVEAU = "nouveau"
    ENVOYE_AU_RAPPORT = "envoye_au_rapport"
    JUGE_PERTINENT = "juge_pertinent"
    JUGE_NON_PERTINENT = "juge_non_pertinent"
    INCERTAIN = "incertain"  # score de confiance linguistique insuffisant (§5.5.4)


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    channel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("channels.id"))
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id"))
    offer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("offers.id"), nullable=True)
    report_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("reports.id"), nullable=True)

    texte_source: Mapped[str] = mapped_column(Text)
    url_source: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    auteur: Mapped[str | None] = mapped_column(String(255), nullable=True)

    langue_detectee: Mapped[LangueDetectee] = mapped_column(Enum(LangueDetectee))
    expressions_argot_matchees: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    score_pertinence: Mapped[float] = mapped_column(Float)
    score_confiance_linguistique: Mapped[float] = mapped_column(Float)
    statut: Mapped[StatutSignal] = mapped_column(Enum(StatutSignal), default=StatutSignal.NOUVEAU)

    date_detection: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    report: Mapped["Report | None"] = relationship(back_populates="signals")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id"))
    periode_debut: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    periode_fin: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    envoye_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    signals: Mapped[list["Signal"]] = relationship(back_populates="report")
