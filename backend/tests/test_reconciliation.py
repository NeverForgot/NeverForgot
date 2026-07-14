from datetime import datetime, timedelta

from trakist.services.reconciliation.state_machine import ArticleQueue, ReservationStatut


def test_paiement_confirme_libere_la_file() -> None:
    queue = ArticleQueue(article_ref="robe-001", fenetre_expiration=timedelta(minutes=5))

    r1 = queue.ajouter_commentaire("marie")
    assert queue.reservation_active is r1
    assert r1.statut == ReservationStatut.PAIEMENT_DEMANDE

    queue.confirmer_paiement(r1)

    assert r1.statut == ReservationStatut.CONFIRMEE
    assert queue.reservation_active is None


def test_expiration_libere_au_suivant() -> None:
    queue = ArticleQueue(article_ref="robe-001", fenetre_expiration=timedelta(minutes=5))

    r1 = queue.ajouter_commentaire("marie")
    r2 = queue.ajouter_commentaire("awa")
    assert queue.reservation_active is r1
    assert r2.statut == ReservationStatut.EN_ATTENTE

    now_apres_expiration = datetime.utcnow() + timedelta(minutes=6)
    libere = queue.expirer_si_depasse(now=now_apres_expiration)

    assert libere is True
    assert r1.statut == ReservationStatut.EXPIREE
    assert queue.reservation_active is r2
    assert r2.statut == ReservationStatut.PAIEMENT_DEMANDE


def test_expiration_sans_reservation_active_ne_fait_rien() -> None:
    queue = ArticleQueue(article_ref="robe-001", fenetre_expiration=timedelta(minutes=5))
    assert queue.expirer_si_depasse() is False
