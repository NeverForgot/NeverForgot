from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from trakist.api.main import app
from trakist.config import get_settings
from trakist.db import get_db
from trakist.models.business import Business, Channel

_WEBHOOK_HEADERS = {"X-Webhook-Secret": get_settings().webhook_shared_secret}


def _client(db_session: Session) -> TestClient:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_flux_live_bout_en_bout(db_session: Session, business: Business, channel: Channel) -> None:
    client = _client(db_session)
    try:
        resp = client.post(
            "/live-sessions", json={"business_id": str(business.id), "channel_id": str(channel.id)}
        )
        assert resp.status_code == 201
        live_session_id = resp.json()["id"]

        resp = client.post(
            f"/live-sessions/{live_session_id}/comments",
            json={"auteur": "marie", "texte": "Je le veux !", "article_ref": "robe-001"},
        )
        assert resp.status_code == 201
        comment = resp.json()
        assert comment["statut"] == "reserve"
        reservation = comment["reservation"]
        assert reservation["statut"] == "paiement_demande"
        reference = reservation["transaction"]["reference_externe"]

        resp = client.post(
            "/webhooks/payments/momo", json={"reference_externe": reference}, headers=_WEBHOOK_HEADERS
        )
        assert resp.status_code == 200
        assert resp.json()["statut"] == "confirmee"

        resp = client.get(f"/live-sessions/{live_session_id}/journal")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
    finally:
        app.dependency_overrides.clear()
