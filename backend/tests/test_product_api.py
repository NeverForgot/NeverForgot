from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from trakist.api.main import app
from trakist.db import get_db


def _client(db_session: Session) -> TestClient:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_creer_et_lister_des_produits(db_session: Session) -> None:
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
        business_id = resp.json()["id"]

        resp = client.post(
            f"/businesses/{business_id}/products",
            json={"reference": "robe-001", "libelle": "Robe wax", "prix": 15000, "devise": "XOF"},
        )
        assert resp.status_code == 201
        product = resp.json()
        assert product["business_id"] == business_id
        assert product["prix"] == 15000
        assert product["actif"] is True

        resp = client.get(f"/businesses/{business_id}/products")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
    finally:
        app.dependency_overrides.clear()


def test_produit_404_si_business_inconnu(db_session: Session) -> None:
    client = _client(db_session)
    try:
        inconnu = "00000000-0000-0000-0000-000000000000"
        resp = client.post(
            f"/businesses/{inconnu}/products",
            json={"reference": "robe-001", "libelle": "Robe wax", "prix": 15000},
        )
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_produit_409_si_reference_deja_utilisee(db_session: Session) -> None:
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
        business_id = resp.json()["id"]

        payload = {"reference": "robe-001", "libelle": "Robe wax", "prix": 15000}
        resp = client.post(f"/businesses/{business_id}/products", json=payload)
        assert resp.status_code == 201

        resp = client.post(f"/businesses/{business_id}/products", json=payload)
        assert resp.status_code == 409
    finally:
        app.dependency_overrides.clear()
