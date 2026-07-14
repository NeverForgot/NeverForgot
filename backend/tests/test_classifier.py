from trakist.services.classification.classifier import RuleBasedFallbackClassifier
from trakist.services.classification.prompt import OfferContext
from trakist.services.market_context.glossary import GlossaryService
from trakist.services.market_context.language import Langue


def test_classify_message_avec_mots_cles_et_argot(glossary_service: GlossaryService) -> None:
    classifier = RuleBasedFallbackClassifier(glossary_service)
    offer = OfferContext(libelle="Robe wax", mots_cles=["robe", "wax"], secteur="mode")

    result = classifier.classify("Je suis chaud pour la robe wax, combien ?", offer, country_code="CI")

    assert "chaud" in result.expressions_argot_matchees
    assert result.score_pertinence > 0
    assert result.score_confiance_linguistique == 0.85


def test_classify_message_mixte_sans_argot_connu_baisse_la_confiance(glossary_service: GlossaryService) -> None:
    classifier = RuleBasedFallbackClassifier(glossary_service)
    offer = OfferContext(libelle="Robe wax", mots_cles=["robe"], secteur="mode")

    result = classifier.classify("Let's go, je suis dispo pour la commande", offer, country_code="BJ")

    assert result.langue_detectee == Langue.MIXTE
    assert result.expressions_argot_matchees == []
    assert result.score_confiance_linguistique == 0.4


def test_expression_hors_categorie_intention_achat_ne_booste_pas_le_score(
    glossary_service: GlossaryService,
) -> None:
    """'wesh' (fixture conftest.py) est categorise 'autre' : une simple
    interpellation ne doit pas etre traitee comme une intention d'achat."""
    classifier = RuleBasedFallbackClassifier(glossary_service)
    offer = OfferContext(libelle="Robe wax", mots_cles=["robe"], secteur="mode")

    result = classifier.classify("wesh, ca va ?", offer, country_code="CI")

    assert result.expressions_argot_matchees == ["wesh"]
    assert result.score_pertinence == 0.0
