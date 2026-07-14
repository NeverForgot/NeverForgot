"""Construction du prompt de classification, enrichi dynamiquement par pays
et par offre (cahier des charges §5.3 et §5.5) : un seul moteur, un prompt
different par pays plutot qu'un prompt statique unique.
"""

from __future__ import annotations

from dataclasses import dataclass

from trakist.services.market_context.glossary import GlossaryService


@dataclass
class OfferContext:
    libelle: str
    mots_cles: list[str]
    secteur: str
    zone_geo_cible: str | None = None


SYSTEM_PROMPT_TEMPLATE = """Tu es le moteur de classification de Trakist, une plateforme \
de veille commerciale en Afrique de l'Ouest (Benin, Cote d'Ivoire, Senegal).

Ta tache : determiner si le message ci-dessous exprime une intention d'achat \
correspondant a l'offre suivante, en tenant compte du code-switching \
francais/anglais et des expressions d'argot local ci-dessous.

Offre de l'entrepreneur :
- Secteur : {secteur}
- Produit/service : {libelle}
- Mots-cles : {mots_cles}
- Zone ciblee : {zone}

Glossaire d'argot local ({pays}) :
{glossaire}

Consignes :
1. Indique si le message correspond a l'offre (secteur, produit, zone).
2. Indique s'il y a un signal d'intention d'achat, y compris en cas de \
melange francais/anglais ou d'argot local.
3. Donne un score_pertinence entre 0 et 1.
4. Donne un score_confiance_linguistique entre 0 et 1 : si une expression \
n'est pas comprise avec certitude, baisse ce score plutot que de deviner \
en silence.
5. Liste les expressions d'argot du glossaire ci-dessus que tu identifies \
dans le message.
"""


def build_classification_prompt(
    texte_message: str,
    offer: OfferContext,
    country_code: str,
    glossary_service: GlossaryService,
) -> str:
    system = SYSTEM_PROMPT_TEMPLATE.format(
        secteur=offer.secteur,
        libelle=offer.libelle,
        mots_cles=", ".join(offer.mots_cles) or "(aucun)",
        zone=offer.zone_geo_cible or "(non precisee)",
        pays=country_code,
        glossaire=glossary_service.build_prompt_context(country_code) or "(glossaire vide)",
    )
    return f'{system}\nMessage a classifier :\n"""\n{texte_message}\n"""'
