from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from trakist.api.main import app
from trakist.db import get_db
from trakist.models.business import Business, Channel, Offer


def _client(db_session: Session) -> TestClient:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_ingest_message_cree_un_signal(db_session: Session, business: Business, channel: Channel) -> None:
    offer = Offer(business_id=business.id, libelle="Robe wax", mots_cles=["robe", "wax"], zone_geo_cible=None)
    db_session.add(offer)
    db_session.commit()

    client = _client(db_session)
    try:
        resp = client.post(
            f"/channels/{channel.id}/messages",
            json={"texte": "Je suis chaud pour la robe wax, combien ?", "auteur": "Fatou"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["score_pertinence"] > 0
        assert data["statut"] in ("nouveau", "incertain")
    finally:
        app.dependency_overrides.clear()


def test_ingest_message_sans_offer_renvoie_422(db_session: Session, channel: Channel) -> None:
    client = _client(db_session)
    try:
        resp = client.post(f"/channels/{channel.id}/messages", json={"texte": "Bonjour"})
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_ingest_message_channel_inconnu_404(db_session: Session) -> None:
    client = _client(db_session)
    try:
        inconnu = "00000000-0000-0000-0000-000000000000"
        resp = client.post(f"/channels/{inconnu}/messages", json={"texte": "Bonjour"})
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()
