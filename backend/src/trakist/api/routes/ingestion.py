import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from trakist.db import get_db
from trakist.models.business import Channel
from trakist.models.signal import Signal
from trakist.schemas.signal import MessageIngestCreate, SignalOut
from trakist.services.classification.factory import get_classifier
from trakist.services.ingestion.connectors import RawMessage
from trakist.services.ingestion.signal_detection import SignalDetectionService
from trakist.services.market_context.glossary_loader import load_glossary_service

router = APIRouter(tags=["ingestion"])


@router.post("/channels/{channel_id}/messages", response_model=SignalOut, status_code=201)
def ingest_message(
    channel_id: uuid.UUID, payload: MessageIngestCreate, db: Session = Depends(get_db)
) -> Signal:
    """Injecte un message dans le moteur de veille (§3.2) et cree le Signal
    resultant. En production, ce chemin est declenche par un consommateur de
    la file d'ingestion (queue.py) une fois les connecteurs reels branches
    (§5.2) ; expose ici en attendant pour tester/piloter la classification."""
    channel = db.get(Channel, channel_id)
    if channel is None:
        raise HTTPException(status_code=404, detail="Channel introuvable")

    business = channel.business
    glossary_service = load_glossary_service(db, business.country_code)
    classifier = get_classifier(glossary_service)

    raw_message = RawMessage(
        channel_id=str(channel.id),
        auteur=payload.auteur,
        texte=payload.texte,
        url_source=payload.url_source,
        horodatage=datetime.utcnow().isoformat(),
    )

    signal = SignalDetectionService(db, classifier).traiter_message(raw_message, business)
    if signal is None:
        raise HTTPException(
            status_code=422, detail="Aucune Offer declaree pour ce Business : rien a classifier"
        )
    return signal
