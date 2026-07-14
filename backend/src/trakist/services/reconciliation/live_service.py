"""Service de reconciliation live : relie la logique de machine a etats
(state_machine.py) a la persistance (cahier des charges §3.4, §5.4).

Flux : commentaire d'intention d'achat -> reservation -> demande de paiement
(Request-to-Pay) -> confirmation (webhook) ou expiration -> liberation
automatique au suivant de la file pour le meme article. Le "premier de la
file" est determine par ordre d'arrivee du commentaire (LiveComment.horodatage),
pas par ordre d'ecriture en base, pour rester fidele a la regle metier.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from trakist.models.business import Business, Channel, ChannelType
from trakist.models.live import (
    LiveComment,
    LiveSession,
    RailPaiement,
    Reservation,
    StatutComment,
    StatutReservation,
    StatutTransaction,
    Transaction,
)
from trakist.models.product import Product
from trakist.services.payment.momo_orange import PaymentClient
from trakist.timeutils import as_naive_utc, utcnow

logger = logging.getLogger(__name__)

DEFAULT_FENETRE_EXPIRATION = timedelta(minutes=5)
# §6 cahier des charges : commission sur les transactions confirmees via le
# module de reconciliation live TikTok specifiquement (pas les autres rails).
TAUX_COMMISSION_LIVE_TIKTOK = 0.05


class ReconciliationError(Exception):
    pass


class LiveReconciliationService:
    def __init__(
        self,
        db: Session,
        payment_client: PaymentClient | None = None,
        fenetre_expiration: timedelta = DEFAULT_FENETRE_EXPIRATION,
    ) -> None:
        self._db = db
        self._payment_client = payment_client or PaymentClient()
        self._fenetre_expiration = fenetre_expiration

    def ajouter_commentaire(
        self, live_session_id: uuid.UUID, auteur: str, texte: str, article_ref: str
    ) -> LiveComment:
        live_session = self._db.get(LiveSession, live_session_id)
        if live_session is None:
            raise ReconciliationError("Live session introuvable.")

        comment = LiveComment(
            live_session_id=live_session_id,
            auteur=auteur,
            texte=texte,
            statut=StatutComment.EN_FILE,
        )
        comment.reservation = Reservation(article_ref=article_ref)
        self._db.add(comment)
        self._db.flush()

        if self._reservation_active(live_session_id, article_ref) is None:
            self._activer(comment.reservation, live_session.business_id)

        self._db.commit()
        self._db.refresh(comment)
        return comment

    def confirmer_paiement(self, reservation_id: uuid.UUID, reference_externe: str) -> Reservation:
        reservation = self._db.get(Reservation, reservation_id)
        if reservation is None:
            raise ReconciliationError("Reservation introuvable.")
        if reservation.statut != StatutReservation.PAIEMENT_DEMANDE:
            raise ReconciliationError(f"Transition invalide depuis {reservation.statut}.")
        if reservation.transaction is None or reservation.transaction.reference_externe != reference_externe:
            raise ReconciliationError("Reference de transaction inconnue pour cette reservation.")

        reservation.transaction.statut = StatutTransaction.CONFIRMEE
        reservation.transaction.webhook_recu_at = utcnow()
        reservation.transaction.commission_montant = self._commission_si_applicable(reservation)
        reservation.statut = StatutReservation.CONFIRMEE
        reservation.live_comment.statut = StatutComment.CONFIRME

        self._db.commit()
        self._db.refresh(reservation)
        return reservation

    def expirer_et_liberer(
        self, reservation_id: uuid.UUID, now: datetime | None = None
    ) -> Reservation | None:
        now = now or utcnow()
        reservation = self._db.get(Reservation, reservation_id)
        if reservation is None:
            raise ReconciliationError("Reservation introuvable.")
        if reservation.statut != StatutReservation.PAIEMENT_DEMANDE:
            return None
        if reservation.expires_at is None or as_naive_utc(now) < as_naive_utc(reservation.expires_at):
            return None

        reservation.statut = StatutReservation.EXPIREE
        reservation.live_comment.statut = StatutComment.EXPIRE
        if reservation.transaction is not None:
            reservation.transaction.statut = StatutTransaction.EXPIREE

        live_session = reservation.live_comment.live_session
        prochaine = self._prochaine_en_attente(live_session.id, reservation.article_ref)
        if prochaine is not None:
            self._activer(prochaine, live_session.business_id)

        self._db.commit()
        self._db.refresh(reservation)
        return reservation

    def expirer_toutes_dues(self, now: datetime | None = None) -> list[Reservation]:
        """A appeler periodiquement (ordonnanceur interne, `scheduler.py`) :
        expire toutes les reservations dont la fenetre de paiement est
        depassee et libere le suivant de la file pour chacune."""
        now = now or utcnow()
        stmt = select(Reservation).where(
            Reservation.statut == StatutReservation.PAIEMENT_DEMANDE,
            Reservation.expires_at.is_not(None),
            Reservation.expires_at <= now,
        )
        dues = list(self._db.execute(stmt).scalars())
        return [
            reservation
            for reservation_id in [r.id for r in dues]
            if (reservation := self.expirer_et_liberer(reservation_id, now)) is not None
        ]

    def _reservation_active(self, live_session_id: uuid.UUID, article_ref: str) -> Reservation | None:
        stmt = (
            select(Reservation)
            .join(LiveComment)
            .where(
                LiveComment.live_session_id == live_session_id,
                Reservation.article_ref == article_ref,
                Reservation.statut == StatutReservation.PAIEMENT_DEMANDE,
            )
        )
        return self._db.execute(stmt).scalars().first()

    def _prochaine_en_attente(self, live_session_id: uuid.UUID, article_ref: str) -> Reservation | None:
        stmt = (
            select(Reservation)
            .join(LiveComment)
            .where(
                LiveComment.live_session_id == live_session_id,
                Reservation.article_ref == article_ref,
                Reservation.statut == StatutReservation.EN_ATTENTE,
            )
            .order_by(LiveComment.horodatage.asc())
        )
        return self._db.execute(stmt).scalars().first()

    def _activer(self, reservation: Reservation, business_id: uuid.UUID) -> None:
        now = utcnow()
        reservation.statut = StatutReservation.PAIEMENT_DEMANDE
        reservation.expires_at = now + self._fenetre_expiration
        reservation.live_comment.statut = StatutComment.RESERVE

        business = self._db.get(Business, business_id)
        montant, devise = self._prix_article(business_id, reservation.article_ref)
        resultat = self._payment_client.request_to_pay(
            numero_paiement=business.numero_paiement_momo if business else "",
            montant=montant,
            devise=devise,
            rail=RailPaiement.MOMO,
        )
        reservation.transaction = Transaction(
            rail=RailPaiement.MOMO,
            montant=montant,
            devise=devise,
            statut=StatutTransaction.INITIEE,
            reference_externe=resultat.reference_externe,
        )
        self._db.flush()

    def _prix_article(self, business_id: uuid.UUID, article_ref: str) -> tuple[float, str]:
        stmt = select(Product).where(Product.business_id == business_id, Product.reference == article_ref)
        produit = self._db.execute(stmt).scalars().first()
        if produit is None:
            # Reservation quand meme activee (l'entrepreneur peut cataloguer
            # le produit apres coup) : un article non catalogue ne doit pas
            # bloquer un live en cours, seulement rester tracable pour
            # correction manuelle du montant avant paiement reel.
            logger.warning(
                "Aucun produit trouve pour la reference '%s' (business %s) : montant de "
                "transaction a 0.0 en attendant catalogage.",
                article_ref,
                business_id,
            )
            return 0.0, "XOF"
        return float(produit.prix), produit.devise

    def _commission_si_applicable(self, reservation: Reservation) -> float | None:
        live_session = reservation.live_comment.live_session
        channel = self._db.get(Channel, live_session.channel_id)
        if channel is None or channel.type != ChannelType.TIKTOK_OWN:
            return None
        return round(float(reservation.transaction.montant) * TAUX_COMMISSION_LIVE_TIKTOK, 2)
