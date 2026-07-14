from sqlalchemy.orm import Session

from trakist.models.market import GlossaryCategorie, GlossaryEntry, GlossarySource
from trakist.services.market_context.glossary_loader import load_glossary_service


def test_load_glossary_service_fusionne_socle_et_pays(db_session: Session) -> None:
    db_session.add_all(
        [
            GlossaryEntry(
                country_code=None,
                expression="chaud",
                signification="tres motive",
                categorie=GlossaryCategorie.INTENTION_ACHAT,
                source=GlossarySource.CURATION_MANUELLE,
            ),
            GlossaryEntry(
                country_code="CI",
                expression="wesh",
                signification="interpellation familiere",
                categorie=GlossaryCategorie.AUTRE,
                source=GlossarySource.CURATION_MANUELLE,
            ),
            GlossaryEntry(
                country_code="SN",
                expression="waw",
                signification="oui",
                categorie=GlossaryCategorie.INTENTION_ACHAT,
                source=GlossarySource.CURATION_MANUELLE,
            ),
        ]
    )
    db_session.commit()

    service = load_glossary_service(db_session, "CI")
    expressions = {e.expression for e in service.for_country("CI")}

    assert expressions == {"chaud", "wesh"}
