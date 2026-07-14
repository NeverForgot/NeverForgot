"""Machine a etats du module de reconciliation live (cahier des charges §3.4,
§5.4). Flux : commentaire d'intention d'achat -> reservation en file ->
demande de paiement (Request-to-Pay) -> confirmation (webhook) ou expiration
-> liberation au suivant. Logique pure, independante de la base de donnees,
pour permettre des tests unitaires rapides (paiement confirme, expiration).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class ReservationStatut(str, Enum):
    EN_ATTENTE = "en_attente"
    PAIEMENT_DEMANDE = "paiement_demande"
    CONFIRMEE = "confirmee"
    EXPIREE = "expiree"
    LIBEREE = "liberee"


class TransitionInvalide(Exception):
    pass


@dataclass
class Reservation:
    article_ref: str
    auteur: str
    statut: ReservationStatut = ReservationStatut.EN_ATTENTE
    expires_at: datetime | None = None


@dataclass
class ArticleQueue:
    """File d'attente ordonnee par ordre d'arrivee pour un article donne."""

    article_ref: str
    fenetre_expiration: timedelta
    file: list[Reservation] = field(default_factory=list)
    reservation_active: Reservation | None = None

    def ajouter_commentaire(self, auteur: str) -> Reservation:
        reservation = Reservation(article_ref=self.article_ref, auteur=auteur)
        self.file.append(reservation)
        if self.reservation_active is None:
            self._activer_prochaine()
        return reservation

    def _activer_prochaine(self, now: datetime | None = None) -> None:
        if not self.file:
            self.reservation_active = None
            return
        now = now or datetime.utcnow()
        reservation = self.file.pop(0)
        reservation.statut = ReservationStatut.PAIEMENT_DEMANDE
        reservation.expires_at = now + self.fenetre_expiration
        self.reservation_active = reservation

    def confirmer_paiement(self, reservation: Reservation) -> None:
        if reservation is not self.reservation_active:
            raise TransitionInvalide("Seule la reservation active peut etre confirmee.")
        if reservation.statut != ReservationStatut.PAIEMENT_DEMANDE:
            raise TransitionInvalide(f"Transition invalide depuis {reservation.statut}.")
        reservation.statut = ReservationStatut.CONFIRMEE
        self.reservation_active = None

    def expirer_si_depasse(self, now: datetime | None = None) -> bool:
        """Libere la reservation active si la fenetre est depassee. Renvoie True si liberation."""
        now = now or datetime.utcnow()
        if self.reservation_active is None:
            return False
        if self.reservation_active.statut != ReservationStatut.PAIEMENT_DEMANDE:
            return False
        if self.reservation_active.expires_at is None or now < self.reservation_active.expires_at:
            return False

        self.reservation_active.statut = ReservationStatut.EXPIREE
        self.reservation_active = None
        self._activer_prochaine(now=now)
        return True
