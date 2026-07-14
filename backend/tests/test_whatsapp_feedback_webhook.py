from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from trakist.api.main import app
from trakist.db import get_db
from trakist.models.business import Business, Channel
from trakist.models.signal import LangueDetectee, Signal, StatutSignal


def _client(db_session: Session) -> TestClient:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def _signal(db_session: Session, business: Business, channel: Channel) -> Signal:
    signal = Signal(
        channel_id=channel.id,
        business_id=business.id,
        texte_source="Je suis chaud pour la robe",
        langue_detectee=LangueDetectee.FR,
        score_pertinence=0.8,
        score_confiance_linguistique=0.9,
        statut=StatutSignal.NOUVEAU,
    )
    db_session.add(signal)
    db_session.commit()
    db_session.refresh(signal)
    return signal


def test_webhook_oui_marque_le_signal_pertinent(
    db_session: Session, business: Business, channel: Channel
) -> None:
    signal = _signal(db_session, business, channel)
    client = _client(db_session)
    try:
        resp = client.post(
            "/webhooks/whatsapp/feedback",
            json={"texte": f"OUI (ref {signal.id})"},
        )
        assert resp.status_code == 200
        assert resp.json()["statut"] == "juge_pertinent"
    finally:
        app.dependency_overrides.clear()


def test_webhook_non_marque_le_signal_non_pertinent(
    db_session: Session, business: Business, channel: Channel
) -> None:
    signal = _signal(db_session, business, channel)
    client = _client(db_session)
    try:
        resp = client.post(
            "/webhooks/whatsapp/feedback",
            json={"texte": f"non (ref {signal.id})"},
        )
        assert resp.status_code == 200
        assert resp.json()["statut"] == "juge_non_pertinent"
    finally:
        app.dependency_overrides.clear()


def test_webhook_message_non_parsable_renvoie_422(db_session: Session) -> None:
    client = _client(db_session)
    try:
        resp = client.post("/webhooks/whatsapp/feedback", json={"texte": "bonjour"})
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_webhook_signal_inconnu_renvoie_404(db_session: Session) -> None:
    client = _client(db_session)
    try:
        inconnu = "00000000-0000-0000-0000-000000000000"
        resp = client.post("/webhooks/whatsapp/feedback", json={"texte": f"oui (ref {inconnu})"})
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()
