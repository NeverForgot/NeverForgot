"""Verification des webhooks entrants (cahier des charges §5.2).

Provisoire : les webhooks reels (MTN MoMo / Orange Money, WhatsApp Business
Cloud API) signent leurs requetes selon un schema propre a chaque fournisseur,
non implementable sans les identifiants/documentation reels par pays. En
attendant, un secret partage simple protege les deux webhooks exposes
(`/webhooks/payments/momo`, `/webhooks/whatsapp/feedback`) contre une
falsification triviale (confirmation de paiement forgee, feedback usurpe).
"""

from __future__ import annotations

import hmac

from fastapi import Header, HTTPException

from trakist.config import get_settings


def verify_webhook_secret(x_webhook_secret: str | None = Header(default=None)) -> None:
    secret = get_settings().webhook_shared_secret
    if not secret:
        raise HTTPException(status_code=503, detail="Webhook non configure (WEBHOOK_SHARED_SECRET absent).")
    if x_webhook_secret is None or not hmac.compare_digest(x_webhook_secret, secret):
        raise HTTPException(status_code=401, detail="Secret de webhook invalide ou manquant.")
