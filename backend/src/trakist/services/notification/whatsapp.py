"""Livraison des rapports et boucle de correction humaine via WhatsApp
(cahier des charges §3.3, §5.3). Implementation de depart : client qui
journalise l'envoi au lieu d'appeler l'API WhatsApp Business reelle. A
remplacer par un appel HTTP vers l'API officielle une fois les identifiants
entreprise Meta configures.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("trakist.notification.whatsapp")


@dataclass
class ReportLine:
    source: str
    extrait: str
    url: str | None
    score_pertinence: float
    action_suggeree: str


class WhatsAppClient:
    def __init__(self, api_token: str = "", phone_number_id: str = "") -> None:
        self._api_token = api_token
        self._phone_number_id = phone_number_id

    def send_report(self, destinataire: str, lignes: list[ReportLine]) -> None:
        if not lignes:
            logger.info("Aucun signal a rapporter pour %s, envoi ignore.", destinataire)
            return
        corps = "\n\n".join(
            f"[{ligne.source}] {ligne.extrait}\n"
            f"Score: {ligne.score_pertinence:.2f} — {ligne.action_suggeree}"
            + (f"\n{ligne.url}" if ligne.url else "")
            for ligne in lignes
        )
        self._send(destinataire, corps)

    def send_feedback_prompt(self, destinataire: str, signal_id: str, extrait: str) -> None:
        self._send(
            destinataire,
            f"Prospect: {extrait}\nPertinent ? Reponds OUI ou NON (ref {signal_id}).",
        )

    def _send(self, destinataire: str, corps: str) -> None:
        if not self._api_token:
            logger.info("[stub WhatsApp] -> %s:\n%s", destinataire, corps)
            return
        raise NotImplementedError("Brancher l'appel HTTP a l'API WhatsApp Business officielle.")
