import pytest

from trakist.services.market_context.glossary import GlossaryEntryData, GlossaryService


@pytest.fixture
def glossary_service() -> GlossaryService:
    entries = [
        GlossaryEntryData("chaud", "tres motive pour acheter", "intention_achat", country_code=None),
        GlossaryEntryData("wesh", "interpellation familiere", "autre", country_code="CI"),
        GlossaryEntryData("first", "je veux etre le premier servi", "intention_achat", country_code="SN"),
    ]
    return GlossaryService(entries)
