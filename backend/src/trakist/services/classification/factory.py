"""Bascule entre le classifieur de secours (regles) et le classifieur LLM
reel, selon la presence d'une cle API Anthropic configuree (§5.3)."""

from __future__ import annotations

from trakist.config import get_settings
from trakist.services.classification.classifier import Classifier, RuleBasedFallbackClassifier
from trakist.services.classification.llm_classifier import AnthropicClassifier
from trakist.services.market_context.glossary import GlossaryService


def get_classifier(glossary_service: GlossaryService) -> Classifier:
    settings = get_settings()
    if settings.anthropic_api_key:
        return AnthropicClassifier(
            api_key=settings.anthropic_api_key,
            glossary_service=glossary_service,
            model=settings.classification_model,
        )
    return RuleBasedFallbackClassifier(glossary_service)
