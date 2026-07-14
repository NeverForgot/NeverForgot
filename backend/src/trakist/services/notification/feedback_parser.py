"""Parse la reponse d'un entrepreneur a un prompt de feedback WhatsApp
(§3.3), au format genere par WhatsAppClient.send_feedback_prompt : un mot
OUI/NON suivi d'une reference explicite au signal.

Le format exact d'un webhook WhatsApp Business reel (Meta Cloud API) n'est
pas modelise ici — comme pour le webhook de paiement (PaymentWebhookPayload),
l'integration reelle reste a brancher une fois les identifiants disponibles
(§5.2). Ce parseur traite le contenu texte du message une fois extrait,
independamment du point d'entree qui l'a recu.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

_REF_PATTERN = re.compile(r"\(ref ([0-9a-fA-F-]{36})\)")
_MOTS_POSITIFS = {"oui", "yes", "ok"}
_MOTS_NEGATIFS = {"non", "no"}


class FeedbackParseError(Exception):
    pass


@dataclass
class FeedbackParse:
    signal_id: uuid.UUID
    pertinent: bool


def parse_feedback_message(texte: str) -> FeedbackParse:
    match = _REF_PATTERN.search(texte)
    if match is None:
        raise FeedbackParseError("Aucune reference de signal trouvee dans le message.")

    mots = texte.strip().split()
    premier_mot = mots[0].lower() if mots else ""
    if premier_mot in _MOTS_POSITIFS:
        pertinent = True
    elif premier_mot in _MOTS_NEGATIFS:
        pertinent = False
    else:
        raise FeedbackParseError(f"Reponse non reconnue comme OUI/NON : {premier_mot!r}")

    return FeedbackParse(signal_id=uuid.UUID(match.group(1)), pertinent=pertinent)
