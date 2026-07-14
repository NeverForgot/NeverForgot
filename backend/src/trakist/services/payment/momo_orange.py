"""Client de paiement Request-to-Pay MTN MoMo / Orange Money (cahier des
charges §3.4, §5.2). Implementation de depart : stub qui journalise la
demande et renvoie une reference simulee, en l'absence d'identifiants d'API
configures. A remplacer par l'appel HTTP officiel une fois les identifiants
obtenus (disponibilite du rail a verifier pays par pays, §7).
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from trakist.models.live import RailPaiement

logger = logging.getLogger("trakist.payment")


@dataclass
class RequestToPayResult:
    reference_externe: str


class PaymentClient:
    def __init__(self, api_credentials: str = "") -> None:
        self._api_credentials = api_credentials

    def request_to_pay(
        self, numero_paiement: str, montant: float, devise: str, rail: RailPaiement
    ) -> RequestToPayResult:
        if not self._api_credentials:
            reference = f"stub-{uuid.uuid4()}"
            logger.info(
                "[stub %s] Request-to-Pay %.2f %s vers %s -> ref %s",
                rail.value, montant, devise, numero_paiement, reference,
            )
            return RequestToPayResult(reference_externe=reference)
        raise NotImplementedError(
            "Brancher l'appel Request-to-Pay reel MTN MoMo / Orange Money."
        )
