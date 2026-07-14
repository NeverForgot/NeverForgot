from trakist.config import get_settings
from trakist.services.classification.classifier import RuleBasedFallbackClassifier
from trakist.services.classification.factory import get_classifier
from trakist.services.classification.llm_classifier import AnthropicClassifier
from trakist.services.market_context.glossary import GlossaryService


def test_sans_cle_api_renvoie_le_fallback_par_regles(
    glossary_service: GlossaryService, monkeypatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    get_settings.cache_clear()

    classifier = get_classifier(glossary_service)

    assert isinstance(classifier, RuleBasedFallbackClassifier)
    get_settings.cache_clear()


def test_avec_cle_api_renvoie_le_classifieur_llm(
    glossary_service: GlossaryService, monkeypatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123")
    get_settings.cache_clear()

    classifier = get_classifier(glossary_service)

    assert isinstance(classifier, AnthropicClassifier)
    get_settings.cache_clear()
