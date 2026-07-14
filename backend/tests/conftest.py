import os
from datetime import datetime, timedelta

# Doit etre positionne avant le premier import de trakist.config (lru_cache) :
# les webhooks (api/security.py) sont fail-closed sans secret configure.
os.environ.setdefault("WEBHOOK_SHARED_SECRET", "test-secret-not-for-prod")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from trakist.db import Base
from trakist.models.business import Business, Channel, ChannelType
from trakist.services.market_context.glossary import GlossaryEntryData, GlossaryService

# Toutes les colonnes ARRAY (specifiques Postgres) ont un variant JSON sous
# SQLite (cf. models/*.py), donc l'ensemble du schema est testable en memoire
# ici sans dependre d'une instance Postgres.
_SQLITE_COMPATIBLE_TABLES = [
    "countries",
    Business.__table__,
    Channel.__table__,
    "offers",
    "products",
    "glossary_entries",
    "signals",
    "reports",
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
        numero_whatsapp="2250700000000",
        # Anterieur explicitement : CURRENT_TIMESTAMP sous SQLite n'a pas de
        # fraction de seconde, contrairement aux valeurs Python liees en
        # parametre de requete (toujours ".000000"). Compares au meme
        # instant (business puis signal crees dans la meme seconde de test),
        # la comparaison SQL >= devient une comparaison de chaines qui echoue
        # a tort. Sans impact sous Postgres (timestamp natif, pas de
        # comparaison de chaines) — artefact propre aux tests SQLite.
        created_at=datetime.utcnow() - timedelta(minutes=1),
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
