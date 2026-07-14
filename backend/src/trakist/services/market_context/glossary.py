"""Chargement et injection du glossaire d'argot par pays (cahier des charges
§5.5.2-3). Le glossaire est structure par country_code, avec un socle partage
(entrees sans country_code) et une couche specifique par pays. GlossaryService
fusionne les deux pour un pays donne et sert a la fois a enrichir le prompt de
classification et a detecter les expressions matchees dans un texte.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class GlossaryEntryData:
    expression: str
    signification: str
    categorie: str
    country_code: str | None = None  # None = socle partage entre les 3 pays


def _contient_expression(texte_lower: str, expression_lower: str) -> bool:
    """Match sur frontiere de mot : une simple sous-chaine ferait matcher
    l'entree 'deal' dans 'l'ideal', ou 'non' dans 'sinon' — frequent en
    francais avec des expressions courtes d'une syllabe."""
    pattern = r"(?<!\w)" + re.escape(expression_lower) + r"(?!\w)"
    return re.search(pattern, texte_lower, flags=re.UNICODE) is not None


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

    def match_entries(self, texte: str, country_code: str) -> list[GlossaryEntryData]:
        """Entrees du glossaire (pays + socle) presentes dans le texte, sur
        frontiere de mot. A utiliser plutot que match_expressions des que la
        categorie de l'entree matchee importe (ex. ponderation du score)."""
        texte_lower = texte.lower()
        return [
            entry
            for entry in self.for_country(country_code)
            if _contient_expression(texte_lower, entry.expression.lower())
        ]

    def match_expressions(self, texte: str, country_code: str) -> list[str]:
        """Expressions du glossaire (pays + socle) presentes dans le texte."""
        return [entry.expression for entry in self.match_entries(texte, country_code)]

    def build_prompt_context(self, country_code: str) -> str:
        """Bloc texte a injecter dans le prompt de classification pour ce pays."""
        lignes = [
            f"- {e.expression} : {e.signification} ({e.categorie})"
            for e in self.for_country(country_code)
        ]
        return "\n".join(lignes)
