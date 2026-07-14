"""Pont entre GlossaryEntry (ORM) et GlossaryService (logique pure, sans
dependance DB — cf. glossary.py). Garde le service de glossaire testable
sans base de donnees tout en permettant de le construire depuis les
donnees reelles en production/API (§5.5.2-3)."""

from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import Session

from trakist.models.market import GlossaryEntry
from trakist.services.market_context.glossary import GlossaryEntryData, GlossaryService


def load_glossary_service(db: Session, country_code: str) -> GlossaryService:
    """Charge le socle partage (country_code NULL) + la couche specifique
    au pays demande, comme decrit au §5.5.2."""
    entries = (
        db.query(GlossaryEntry)
        .filter(or_(GlossaryEntry.country_code == country_code, GlossaryEntry.country_code.is_(None)))
        .all()
    )
    data = [
        GlossaryEntryData(
            expression=entry.expression,
            signification=entry.signification,
            categorie=entry.categorie.value,
            country_code=entry.country_code,
        )
        for entry in entries
    ]
    return GlossaryService(data)
