import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from trakist.db import Base
from trakist.models.business import Business, Channel, ChannelType
from trakist.services.market_context.glossary import GlossaryEntryData, GlossaryService

# Tables sans colonne ARRAY (specifique Postgres) : suffisantes pour tester le
# module de reconciliation live sur SQLite en memoire, sans dependre d'une
# instance Postgres. Countries/Offers/GlossaryEntry (ARRAY) sont hors scope
# de ces tests.
_SQLITE_COMPATIBLE_TABLES = [
    Business.__table__,
    Channel.__table__,
    "live_sessions",
    "live_comments",
    "reservations",
    "transactions",
]


@pytest.fixture
def glossary_service() -> GlossaryService:
    entries = [
        GlossaryEntryData("chaud", "tres motive pour acheter", "intention_achat", country_code=None),
        GlossaryEntryData("wesh", "interpellation familiere", "autre", country_code="CI"),
        GlossaryEntryData("first", "je veux etre le premier servi", "intention_achat", country_code="SN"),
    ]
    return GlossaryService(entries)


@pytest.fixture
def db_session():
    import trakist.models  # noqa: F401  (enregistre toutes les tables sur Base.metadata)

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [
        t if not isinstance(t, str) else Base.metadata.tables[t] for t in _SQLITE_COMPATIBLE_TABLES
    ]
    Base.metadata.create_all(engine, tables=tables)
    session_local = sessionmaker(bind=engine)
    session: Session = session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def business(db_session: Session) -> Business:
    biz = Business(
        nom="Boutique Awa",
        secteur="mode",
        ville="Abidjan",
        country_code="CI",
        numero_paiement_momo="2250700000000",
    )
    db_session.add(biz)
    db_session.commit()
    db_session.refresh(biz)
    return biz


@pytest.fixture
def channel(db_session: Session, business: Business) -> Channel:
    ch = Channel(
        type=ChannelType.TIKTOK_OWN,
        business_id=business.id,
        identifiant_externe="@boutique_awa",
    )
    db_session.add(ch)
    db_session.commit()
    db_session.refresh(ch)
    return ch
