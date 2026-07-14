from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from trakist.api.main import app
from trakist.db import get_db


def _client(db_session: Session) -> TestClient:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_onboarding_complet_business_offer_channel(db_session: Session) -> None:
    client = _client(db_session)
    try:
        resp = client.post(
            "/businesses",
            json={
                "nom": "Boutique Awa",
                "secteur": "mode",
                "ville": "Abidjan",
                "country_code": "CI",
                "numero_paiement_momo": "2250700000000",
                "numero_whatsapp": "2250700000000",
            },
        )
        assert resp.status_code == 201
        business_id = resp.json()["id"]

        resp = client.post(
            f"/businesses/{business_id}/offers",
            json={
                "libelle": "Robe wax",
                "mots_cles": ["robe", "wax"],
                "zone_geo_cible": "Abidjan",
            },
        )
        assert resp.status_code == 201
        offer = resp.json()
        assert offer["business_id"] == business_id
        assert offer["mots_cles"] == ["robe", "wax"]

        resp = client.post(
            f"/businesses/{business_id}/channels",
            json={"type": "tiktok_own", "identifiant_externe": "@boutique_awa"},
        )
        assert resp.status_code == 201
        channel = resp.json()
        assert channel["statut_connexion"] == "connecte"

        resp = client.get(f"/businesses/{business_id}/offers")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        resp = client.get(f"/businesses/{business_id}/channels")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
    finally:
        app.dependency_overrides.clear()


def test_offer_et_channel_404_si_business_inconnu(db_session: Session) -> None:
    client = _client(db_session)
    try:
        inconnu = "00000000-0000-0000-0000-000000000000"
        resp = client.post(f"/businesses/{inconnu}/offers", json={"libelle": "Robe"})
        assert resp.status_code == 404

        resp = client.post(
            f"/businesses/{inconnu}/channels",
            json={"type": "tiktok_own", "identifiant_externe": "@x"},
        )
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()
