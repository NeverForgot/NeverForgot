"""Classification par appel LLM reel (cahier des charges §3.2, §5.3),
derriere la meme interface que RuleBasedFallbackClassifier. Sortie
structuree validee par schema Pydantic (client.messages.parse) plutot que du
parsing manuel de texte libre.

Choix de modele : Haiku 4.5 par defaut (`classification_model` dans les
settings) — volume eleve, prompts courts, tache de classification peu
complexe. A remonter vers un modele plus capable si le taux de pertinence
mesure en cohorte pilote (§2.2) le justifie.
"""

from __future__ import annotations

import logging

import anthropic
from pydantic import BaseModel, Field

from trakist.services.classification.classifier import ClassificationResult
from trakist.services.classification.prompt import OfferContext, build_classification_prompt
from trakist.services.market_context.glossary import GlossaryService
from trakist.services.market_context.language import Langue, LanguageDetector

logger = logging.getLogger("trakist.classification.llm")


class _LLMClassificationOutput(BaseModel):
    correspond_offre: bool
    intention_achat: bool
    score_pertinence: float = Field(ge=0.0, le=1.0)
    score_confiance_linguistique: float = Field(ge=0.0, le=1.0)
    expressions_argot_identifiees: list[str] = Field(default_factory=list)


class AnthropicClassifier:
    """Classification via l'API Claude, sortie contrainte par schema JSON.

    En cas d'echec (erreur API, timeout, refus, sortie non parsable) : renvoie
    un score de confiance de 0.0 plutot que de lever une exception ou de
    deviner — le signal remonte en aval comme 'incertain' (§5.5.4), jamais
    silencieusement pertinent ou non pertinent.
    """

    def __init__(
        self,
        api_key: str,
        glossary_service: GlossaryService,
        model: str = "claude-haiku-4-5",
        language_detector: LanguageDetector | None = None,
        timeout_seconds: float = 15.0,
        client: anthropic.Anthropic | None = None,
    ) -> None:
        self._client = client or anthropic.Anthropic(
            api_key=api_key, timeout=timeout_seconds, max_retries=2
        )
        self._model = model
        self._glossary = glossary_service
        self._language_detector = language_detector or LanguageDetector()

    def classify(
        self, texte_message: str, offer: OfferContext, country_code: str
    ) -> ClassificationResult:
        langue_result = self._language_detector.detect(texte_message)
        expressions_glossaire = self._glossary.match_expressions(texte_message, country_code)
        prompt = build_classification_prompt(texte_message, offer, country_code, self._glossary)

        try:
            response = self._client.messages.parse(
                model=self._model,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
                output_format=_LLMClassificationOutput,
            )
        except anthropic.APIError as exc:
            logger.warning("Echec de l'appel de classification LLM, signal marque incertain : %s", exc)
            return self._resultat_incertain(langue_result.langue, expressions_glossaire, prompt)

        if response.stop_reason == "refusal" or response.parsed_output is None:
            logger.warning(
                "Reponse de classification LLM refusee ou non parsable, signal marque incertain."
            )
            return self._resultat_incertain(langue_result.langue, expressions_glossaire, prompt)

        parsed = response.parsed_output
        return ClassificationResult(
            langue_detectee=langue_result.langue,
            expressions_argot_matchees=parsed.expressions_argot_identifiees or expressions_glossaire,
            score_pertinence=parsed.score_pertinence,
            score_confiance_linguistique=parsed.score_confiance_linguistique,
            prompt_utilise=prompt,
        )

    @staticmethod
    def _resultat_incertain(
        langue: Langue, expressions_glossaire: list[str], prompt: str
    ) -> ClassificationResult:
        return ClassificationResult(
            langue_detectee=langue,
            expressions_argot_matchees=expressions_glossaire,
            score_pertinence=0.0,
            score_confiance_linguistique=0.0,
            prompt_utilise=prompt,
        )
