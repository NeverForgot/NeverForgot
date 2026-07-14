"""Catalogue produit minimal (cahier des charges §3.4, §4) : relie une
`Reservation.article_ref` (saisie libre par l'entrepreneur pendant un live)
a un prix reel, pour sortir le montant de transaction du placeholder `0.0`
et permettre le calcul de la commission sur les ventes live (§6)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from trakist.db import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("business_id", "reference", name="uq_products_business_reference"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id"))
    # Doit correspondre a Reservation.article_ref pour etre trouve a l'activation
    # d'une reservation (live_service.py) — pas de cle etrangere directe : un
    # article_ref peut etre saisi avant que le produit correspondant n'existe.
    reference: Mapped[str] = mapped_column(String(255))
    libelle: Mapped[str] = mapped_column(String(255))
    prix: Mapped[float] = mapped_column(Numeric(12, 2))
    devise: Mapped[str] = mapped_column(String(3), default="XOF")
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    business: Mapped["Business"] = relationship(back_populates="products")
