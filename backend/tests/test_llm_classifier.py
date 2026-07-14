from dataclasses import dataclass, field

import anthropic
import httpx

from trakist.services.classification.llm_classifier import (
    AnthropicClassifier,
    _LLMClassificationOutput,
)
from trakist.services.classification.prompt import OfferContext
from trakist.services.market_context.glossary import GlossaryService
from trakist.services.market_context.language import Langue


@dataclass
class _FakeParsedResponse:
    stop_reason: str
    parsed_output: _LLMClassificationOutput | None


@dataclass
class _FakeMessagesResource:
    responses: list[_FakeParsedResponse] = field(default_factory=list)
    exception: Exception | None = None

    def parse(self, **kwargs):
        if self.exception is not None:
            raise self.exception
        return self.responses.pop(0)


@dataclass
class _FakeAnthropicClient:
    messages: _FakeMessagesResource


def test_classify_succes_retourne_la_sortie_structuree(glossary_service: GlossaryService) -> None:
    parsed = _LLMClassificationOutput(
        correspond_offre=True,
        intention_achat=True,
        score_pertinence=0.9,
        score_confiance_linguistique=0.8,
        expressions_argot_identifiees=["chaud"],
    )
    fake_client = _FakeAnthropicClient(
        messages=_FakeMessagesResource(responses=[_FakeParsedResponse("end_turn", parsed)])
    )
    classifier = AnthropicClassifier(
        api_key="test", glossary_service=glossary_service, client=fake_client
    )
    offer = OfferContext(libelle="Robe wax", mots_cles=["robe"], secteur="mode")

    result = classifier.classify("Je suis chaud pour la robe wax", offer, country_code="CI")

    assert result.score_pertinence == 0.9
    assert result.score_confiance_linguistique == 0.8
    assert result.expressions_argot_matchees == ["chaud"]


def test_classify_refus_llm_marque_incertain(glossary_service: GlossaryService) -> None:
    fake_client = _FakeAnthropicClient(
        messages=_FakeMessagesResource(responses=[_FakeParsedResponse("refusal", None)])
    )
    classifier = AnthropicClassifier(
        api_key="test", glossary_service=glossary_service, client=fake_client
    )
    offer = OfferContext(libelle="Robe wax", mots_cles=["robe"], secteur="mode")

    result = classifier.classify("Je suis chaud pour la robe wax", offer, country_code="CI")

    assert result.score_pertinence == 0.0
    assert result.score_confiance_linguistique == 0.0


def test_classify_erreur_api_marque_incertain_sans_lever(glossary_service: GlossaryService) -> None:
    fake_request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    fake_client = _FakeAnthropicClient(
        messages=_FakeMessagesResource(exception=anthropic.APIConnectionError(request=fake_request))
    )
    classifier = AnthropicClassifier(
        api_key="test", glossary_service=glossary_service, client=fake_client
    )
    offer = OfferContext(libelle="Robe wax", mots_cles=["robe"], secteur="mode")

    result = classifier.classify("Je suis chaud pour la robe wax", offer, country_code="CI")

    assert result.score_confiance_linguistique == 0.0
    assert result.langue_detectee == Langue.FR
