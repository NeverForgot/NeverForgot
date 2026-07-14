import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from trakist.api.main import app
from trakist.db import get_db
from trakist.models.business import Business, Channel, ChannelType, StatutConnexion
from trakist.models.signal import LangueDetectee, Signal, StatutSignal
from trakist.services.admin.dashboard import sante_connecteurs, taux_pertinence_par_cohorte


def _business(db_session: Session, country_code: str, secteur: str, numero: str) -> Business:
    biz = Business(
        nom=f"Boutique {numero}",
        secteur=secteur,
        ville="Ville",
        country_code=country_code,
        numero_paiement_momo=numero,
        numero_whatsapp=numero,
    )
    db_session.add(biz)
    db_session.commit()
    db_session.refresh(biz)
    return biz


def _channel(db_session: Session, business: Business, statut=StatutConnexion.CONNECTE) -> Channel:
    ch = Channel(
        type=ChannelType.FACEBOOK_GROUP,
        business_id=business.id,
        identifiant_externe="grp",
        statut_connexion=statut,
    )
    db_session.add(ch)
    db_session.commit()
    db_session.refresh(ch)
    return ch


def _signal(db_session: Session, business: Business, channel: Channel, statut: StatutSignal) -> Signal:
    signal = Signal(
        channel_id=channel.id,
        business_id=business.id,
        texte_source="texte",
        langue_detectee=LangueDetectee.FR,
        score_pertinence=0.5,
        score_confiance_linguistique=0.9,
        statut=statut,
    )
    db_session.add(signal)
    db_session.commit()
    return signal


def test_taux_pertinence_par_cohorte(db_session: Session) -> None:
    biz_ci_mode = _business(db_session, "CI", "mode", "1")
    ch_ci_mode = _channel(db_session, biz_ci_mode)
    for _ in range(4):
        _signal(db_session, biz_ci_mode, ch_ci_mode, StatutSignal.JUGE_PERTINENT)
    _signal(db_session, biz_ci_mode, ch_ci_mode, StatutSignal.JUGE_NON_PERTINENT)

    biz_ci_agro = _business(db_session, "CI", "agroalimentaire", "2")
    ch_ci_agro = _channel(db_session, biz_ci_agro)
    _signal(db_session, biz_ci_agro, ch_ci_agro, StatutSignal.JUGE_PERTINENT)
    _signal(db_session, biz_ci_agro, ch_ci_agro, StatutSignal.JUGE_NON_PERTINENT)
    _signal(db_session, biz_ci_agro, ch_ci_agro, StatutSignal.JUGE_NON_PERTINENT)

    biz_sn_mode = _business(db_session, "SN", "mode", "3")
    ch_sn_mode = _channel(db_session, biz_sn_mode)
    _signal(db_session, biz_sn_mode, ch_sn_mode, StatutSignal.NOUVEAU)

    resultats = {(r.country_code, r.secteur): r for r in taux_pertinence_par_cohorte(db_session)}

    ci_mode = resultats[("CI", "mode")]
    assert ci_mode.nombre_signaux_juges == 5
    assert ci_mode.nombre_pertinents == 4
    assert ci_mode.taux_pertinence == 0.8
    assert ci_mode.seuil_ouverture_large_atteint is True

    ci_agro = resultats[("CI", "agroalimentaire")]
    assert ci_agro.taux_pertinence == pytest.approx(1 / 3)
    assert ci_agro.seuil_ouverture_large_atteint is False

    sn_mode = resultats[("SN", "mode")]
    assert sn_mode.nombre_signaux_juges == 0
    assert sn_mode.taux_pertinence is None
    assert sn_mode.seuil_ouverture_large_atteint is False


def test_sante_connecteurs(db_session: Session) -> None:
    biz = _business(db_session, "CI", "mode", "1")
    _channel(db_session, biz, statut=StatutConnexion.CONNECTE)
    _channel(db_session, biz, statut=StatutConnexion.DECONNECTE)

    resultats = sante_connecteurs(db_session)

    par_statut = {r.statut_connexion: r.nombre for r in resultats if r.country_code == "CI"}
    assert par_statut[StatutConnexion.CONNECTE] == 1
    assert par_statut[StatutConnexion.DECONNECTE] == 1


def test_route_dashboard_pilote(db_session: Session) -> None:
    biz = _business(db_session, "CI", "mode", "1")
    ch = _channel(db_session, biz)
    _signal(db_session, biz, ch, StatutSignal.JUGE_PERTINENT)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)
        resp = client.get("/admin/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["taux_pertinence"][0]["country_code"] == "CI"
        assert data["sante_connecteurs"][0]["country_code"] == "CI"
    finally:
        app.dependency_overrides.clear()
