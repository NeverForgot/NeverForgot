"""Chargement et injection du glossaire d'argot par pays (cahier des charges
§5.5.2-3). Le glossaire est structure par country_code, avec un socle partage
(entrees sans country_code) et une couche specifique par pays. GlossaryService
fusionne les deux pour un pays donne et sert a la fois a enrichir le prompt de
classification et a detecter les expressions matchees dans un texte.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GlossaryEntryData:
    expression: str
    signification: str
    categorie: str
    country_code: str | None = None  # None = socle partage entre les 3 pays


class GlossaryService:
    def __init__(self, entries: list[GlossaryEntryData]) -> None:
        self._entries = entries

    def for_country(self, country_code: str) -> list[GlossaryEntryData]:
        """Socle partage + couche specifique au pays, sans doublon d'expression."""
        specifiques = {e.expression.lower(): e for e in self._entries if e.country_code == country_code}
        partages = {
            e.expression.lower(): e
            for e in self._entries
            if e.country_code is None and e.expression.lower() not in specifiques
        }
        return list(specifiques.values()) + list(partages.values())

    def match_expressions(self, texte: str, country_code: str) -> list[str]:
        """Expressions du glossaire (pays + socle) presentes dans le texte."""
        texte_lower = texte.lower()
        return [
            entry.expression
            for entry in self.for_country(country_code)
            if entry.expression.lower() in texte_lower
        ]

    def build_prompt_context(self, country_code: str) -> str:
        """Bloc texte a injecter dans le prompt de classification pour ce pays."""
        lignes = [
            f"- {e.expression} : {e.signification} ({e.categorie})"
            for e in self.for_country(country_code)
        ]
        return "\n".join(lignes)
