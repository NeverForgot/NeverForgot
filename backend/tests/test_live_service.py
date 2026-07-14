from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from trakist.models.business import Business, Channel, ChannelType
from trakist.models.live import LiveSession, StatutComment, StatutReservation, StatutTransaction
from trakist.models.product import Product
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


def test_expirer_toutes_dues_traite_plusieurs_articles_et_ignore_les_non_dues(
    db_session: Session, live_session: LiveSession
) -> None:
    service = LiveReconciliationService(db_session, fenetre_expiration=timedelta(minutes=5))

    robe = service.ajouter_commentaire(live_session.id, "marie", "Je le veux", "robe-001")
    robe_suivante = service.ajouter_commentaire(live_session.id, "awa", "Moi aussi", "robe-001")
    sac = service.ajouter_commentaire(live_session.id, "fatou", "Je prends", "sac-002")

    now_apres_expiration = datetime.utcnow() + timedelta(minutes=6)
    expirees = service.expirer_toutes_dues(now=now_apres_expiration)

    assert {r.id for r in expirees} == {robe.reservation.id, sac.reservation.id}
    db_session.refresh(robe.reservation)
    db_session.refresh(sac.reservation)
    db_session.refresh(robe_suivante.reservation)
    assert robe.reservation.statut == StatutReservation.EXPIREE
    assert sac.reservation.statut == StatutReservation.EXPIREE
    assert robe_suivante.reservation.statut == StatutReservation.PAIEMENT_DEMANDE


def test_expirer_toutes_dues_ne_fait_rien_si_aucune_reservation_due(
    db_session: Session, live_session: LiveSession
) -> None:
    service = LiveReconciliationService(db_session, fenetre_expiration=timedelta(minutes=5))
    service.ajouter_commentaire(live_session.id, "marie", "Je le veux", "robe-001")

    assert service.expirer_toutes_dues(now=datetime.utcnow()) == []


def test_activation_sans_produit_catalogue_laisse_le_montant_a_zero(
    db_session: Session, live_session: LiveSession
) -> None:
    service = LiveReconciliationService(db_session)

    comment = service.ajouter_commentaire(live_session.id, "marie", "Je le veux", "article-inconnu")

    assert comment.reservation.transaction.montant == 0.0
    assert comment.reservation.transaction.devise == "XOF"


def test_activation_utilise_le_prix_du_produit_catalogue(
    db_session: Session, business: Business, live_session: LiveSession
) -> None:
    produit = Product(business_id=business.id, reference="robe-001", libelle="Robe wax", prix=15000, devise="XOF")
    db_session.add(produit)
    db_session.commit()
    service = LiveReconciliationService(db_session)

    comment = service.ajouter_commentaire(live_session.id, "marie", "Je le veux", "robe-001")

    assert comment.reservation.transaction.montant == 15000.0
    assert comment.reservation.transaction.devise == "XOF"


def test_confirmation_calcule_la_commission_sur_live_tiktok(
    db_session: Session, business: Business, live_session: LiveSession
) -> None:
    """`channel` (conftest.py) est de type TIKTOK_OWN."""
    produit = Product(business_id=business.id, reference="robe-001", libelle="Robe wax", prix=15000, devise="XOF")
    db_session.add(produit)
    db_session.commit()
    service = LiveReconciliationService(db_session)
    comment = service.ajouter_commentaire(live_session.id, "marie", "Je le veux", "robe-001")
    reference = comment.reservation.transaction.reference_externe

    reservation = service.confirmer_paiement(comment.reservation.id, reference)

    assert reservation.transaction.commission_montant == 750.0  # 5% de 15000


def test_confirmation_sans_commission_hors_tiktok(
    db_session: Session, business: Business
) -> None:
    channel = Channel(type=ChannelType.WHATSAPP_GROUP, business_id=business.id, identifiant_externe="grp-42")
    db_session.add(channel)
    db_session.commit()
    db_session.refresh(channel)
    live_session = LiveSession(business_id=business.id, channel_id=channel.id)
    db_session.add(live_session)
    db_session.commit()
    db_session.refresh(live_session)

    service = LiveReconciliationService(db_session)
    comment = service.ajouter_commentaire(live_session.id, "marie", "Je le veux", "sac-001")
    reference = comment.reservation.transaction.reference_externe

    reservation = service.confirmer_paiement(comment.reservation.id, reference)

    assert reservation.transaction.commission_montant is None
