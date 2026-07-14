from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

import trakist.scheduler as scheduler_module
from trakist.models.business import Business, Channel
from trakist.models.live import LiveSession, StatutReservation
from trakist.models.signal import LangueDetectee, Signal, StatutSignal
from trakist.services.reconciliation.live_service import LiveReconciliationService
from trakist.services.notification.whatsapp import WhatsAppClient


class _FakeWhatsAppClient(WhatsAppClient):
    def send_report(self, destinataire: str, lignes: list) -> None:
        pass


@pytest.fixture
def _patch_session_local(monkeypatch: pytest.MonkeyPatch, db_session: Session):
    """`_job_*` ouvrent leur propre session via `SessionLocal()` puis la
    ferment ; on la fait pointer vers la session de test SQLite sans la
    laisser se fermer (les tests continuent de s'en servir apres l'appel)."""

    def _session_local() -> Session:
        return db_session

    monkeypatch.setattr(db_session, "close", lambda: None)
    monkeypatch.setattr(scheduler_module, "SessionLocal", _session_local)


def test_create_scheduler_enregistre_les_deux_jobs() -> None:
    scheduler = scheduler_module.create_scheduler()
    job_ids = {job.id for job in scheduler.get_jobs()}
    assert job_ids == {"generer_rapports", "expirer_reservations"}


def test_job_generer_rapports_envoie_les_rapports_dus(
    _patch_session_local, db_session: Session, business: Business, channel: Channel
) -> None:
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

    scheduler_module._job_generer_rapports()

    db_session.refresh(signal)
    assert signal.statut == StatutSignal.ENVOYE_AU_RAPPORT


def test_job_expirer_reservations_libere_les_reservations_dues(
    _patch_session_local, db_session: Session, business: Business, channel: Channel
) -> None:
    live_session = LiveSession(business_id=business.id, channel_id=channel.id)
    db_session.add(live_session)
    db_session.commit()
    db_session.refresh(live_session)

    service = LiveReconciliationService(db_session, fenetre_expiration=timedelta(minutes=-1))
    comment = service.ajouter_commentaire(live_session.id, "marie", "Je le veux", "robe-001")
    assert comment.reservation.statut == StatutReservation.PAIEMENT_DEMANDE

    scheduler_module._job_expirer_reservations()

    db_session.refresh(comment.reservation)
    assert comment.reservation.statut == StatutReservation.EXPIREE
