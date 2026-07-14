from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from trakist.models.business import Business, Channel
from trakist.models.live import LiveSession, StatutComment, StatutReservation, StatutTransaction
from trakist.services.reconciliation.live_service import (
    LiveReconciliationService,
    ReconciliationError,
)


@pytest.fixture
def live_session(db_session: Session, business: Business, channel: Channel) -> LiveSession:
    session = LiveSession(business_id=business.id, channel_id=channel.id)
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


def test_premier_commentaire_active_directement_la_reservation(
    db_session: Session, live_session: LiveSession
) -> None:
    service = LiveReconciliationService(db_session)

    comment = service.ajouter_commentaire(live_session.id, "marie", "Je le veux !", "robe-001")

    assert comment.statut == StatutComment.RESERVE
    assert comment.reservation.statut == StatutReservation.PAIEMENT_DEMANDE
    assert comment.reservation.expires_at is not None
    assert comment.reservation.transaction is not None
    assert comment.reservation.transaction.statut == StatutTransaction.INITIEE


def test_deuxieme_commentaire_meme_article_reste_en_attente(
    db_session: Session, live_session: LiveSession
) -> None:
    service = LiveReconciliationService(db_session)

    premier = service.ajouter_commentaire(live_session.id, "marie", "Je le veux", "robe-001")
    second = service.ajouter_commentaire(live_session.id, "awa", "Moi aussi", "robe-001")

    assert premier.reservation.statut == StatutReservation.PAIEMENT_DEMANDE
    assert second.statut == StatutComment.EN_FILE
    assert second.reservation.statut == StatutReservation.EN_ATTENTE
    assert second.reservation.transaction is None


def test_paiement_confirme(db_session: Session, live_session: LiveSession) -> None:
    service = LiveReconciliationService(db_session)
    comment = service.ajouter_commentaire(live_session.id, "marie", "Je le veux", "robe-001")
    reference = comment.reservation.transaction.reference_externe

    reservation = service.confirmer_paiement(comment.reservation.id, reference)

    assert reservation.statut == StatutReservation.CONFIRMEE
    assert reservation.live_comment.statut == StatutComment.CONFIRME
    assert reservation.transaction.statut == StatutTransaction.CONFIRMEE


def test_confirmation_avec_mauvaise_reference_echoue(
    db_session: Session, live_session: LiveSession
) -> None:
    service = LiveReconciliationService(db_session)
    comment = service.ajouter_commentaire(live_session.id, "marie", "Je le veux", "robe-001")

    with pytest.raises(ReconciliationError):
        service.confirmer_paiement(comment.reservation.id, "ref-inconnue")


def test_expiration_libere_au_suivant(db_session: Session, live_session: LiveSession) -> None:
    service = LiveReconciliationService(db_session, fenetre_expiration=timedelta(minutes=5))

    premier = service.ajouter_commentaire(live_session.id, "marie", "Je le veux", "robe-001")
    second = service.ajouter_commentaire(live_session.id, "awa", "Moi aussi", "robe-001")

    now_apres_expiration = datetime.utcnow() + timedelta(minutes=6)
    resultat = service.expirer_et_liberer(premier.reservation.id, now=now_apres_expiration)

    assert resultat.statut == StatutReservation.EXPIREE
    db_session.refresh(second.reservation)
    assert second.reservation.statut == StatutReservation.PAIEMENT_DEMANDE
    assert second.reservation.transaction is not None


def test_expiration_avant_la_fenetre_ne_fait_rien(
    db_session: Session, live_session: LiveSession
) -> None:
    service = LiveReconciliationService(db_session, fenetre_expiration=timedelta(minutes=5))
    comment = service.ajouter_commentaire(live_session.id, "marie", "Je le veux", "robe-001")

    resultat = service.expirer_et_liberer(comment.reservation.id, now=datetime.utcnow())

    assert resultat is None
