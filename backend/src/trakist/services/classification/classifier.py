"""Service de classification : construit le prompt (§5.3) et produit un
resultat de classification. L'implementation par defaut est une heuristique
sans dependance externe (fallback), pour que le squelette soit testable sans
cle API LLM configuree. Brancher un Classifier reel (appel LLM) en
implementant la meme interface pour la qualite de classification cible.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from trakist.services.classification.prompt import OfferContext, build_classification_prompt
from trakist.services.market_context.glossary import GlossaryService
from trakist.services.market_context.language import Langue, LanguageDetector


@dataclass
class ClassificationResult:
    langue_detectee: Langue
    expressions_argot_matchees: list[str]
    score_pertinence: float
    score_confiance_linguistique: float
    prompt_utilise: str


class Classifier(Protocol):
    def classify(
        self, texte_message: str, offer: OfferContext, country_code: str
    ) -> ClassificationResult: ...


#  Poids par categorie d'expression du glossaire (GlossaryCategorie) dans le
#  score de pertinence : une expression 'autre' (ex. 'gaou' — moqueur, pas
#  une intention d'achat, cf. seed_glossary.py) ne doit pas booster le score
#  au meme titre qu'une expression 'intention_achat'.
_POIDS_CATEGORIE_GLOSSAIRE = {
    "intention_achat": 0.25,
    "negociation": 0.15,
    "question": 0.1,
    "autre": 0.0,
}


class RuleBasedFallbackClassifier:
    """Classification par mots-cles + glossaire, sans appel LLM.

    Sert de reference/fallback et de socle pour les tests. Un score de
    confiance linguistique bas force le statut 'incertain' en aval plutot que
    de classer silencieusement le signal comme pertinent ou non (§5.5.4).
    """

    def __init__(
        self,
        glossary_service: GlossaryService,
        language_detector: LanguageDetector | None = None,
    ) -> None:
        self._glossary = glossary_service
        self._language_detector = language_detector or LanguageDetector()

    def classify(
        self, texte_message: str, offer: OfferContext, country_code: str
    ) -> ClassificationResult:
        prompt = build_classification_prompt(texte_message, offer, country_code, self._glossary)

        langue_result = self._language_detector.detect(texte_message)
        entrees_matchees = self._glossary.match_entries(texte_message, country_code)
        expressions_matchees = [entry.expression for entry in entrees_matchees]

        texte_lower = texte_message.lower()
        mots_cles_matches = sum(1 for mc in offer.mots_cles if mc.lower() in texte_lower)
        poids_glossaire = sum(
            _POIDS_CATEGORIE_GLOSSAIRE.get(entry.categorie, 0.0) for entry in entrees_matchees
        )
        score_pertinence = min(1.0, 0.3 * mots_cles_matches + poids_glossaire)

        # Confiance basse si le message est un melange de langues sans
        # qu'aucune expression du glossaire ne l'explique : signal a verifier
        # humainement pendant la phase pilote plutot qu'a classer en silence.
        if langue_result.langue == Langue.MIXTE and not expressions_matchees:
            score_confiance = 0.4
        else:
            score_confiance = 0.85

        return ClassificationResult(
            langue_detectee=langue_result.langue,
            expressions_argot_matchees=expressions_matchees,
            score_pertinence=round(score_pertinence, 2),
            score_confiance_linguistique=score_confiance,
            prompt_utilise=prompt,
        )
