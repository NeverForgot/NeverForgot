import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from trakist.db import get_db
from trakist.models.signal import Signal, StatutSignal
from trakist.schemas.signal import SignalFeedback, SignalOut, WhatsAppInboundMessage
from trakist.services.notification.feedback_parser import FeedbackParseError, parse_feedback_message

router = APIRouter(tags=["signals"])


def _appliquer_feedback(db: Session, signal_id: uuid.UUID, pertinent: bool) -> Signal:
    signal = db.get(Signal, signal_id)
    if signal is None:
        raise HTTPException(status_code=404, detail="Signal introuvable")
    signal.statut = StatutSignal.JUGE_PERTINENT if pertinent else StatutSignal.JUGE_NON_PERTINENT
    db.commit()
    db.refresh(signal)
    return signal


@router.get("/businesses/{business_id}/signals", response_model=list[SignalOut])
def list_signals(
    business_id: uuid.UUID,
    statut: StatutSignal | None = None,
    db: Session = Depends(get_db),
) -> list[Signal]:
    query = db.query(Signal).filter(Signal.business_id == business_id)
    if statut:
        query = query.filter(Signal.statut == statut)
    return query.order_by(Signal.date_detection.desc()).all()


@router.post("/signals/{signal_id}/feedback", response_model=SignalOut)
def submit_feedback(signal_id: uuid.UUID, payload: SignalFeedback, db: Session = Depends(get_db)) -> Signal:
    return _appliquer_feedback(db, signal_id, payload.pertinent)


@router.post("/webhooks/whatsapp/feedback", response_model=SignalOut)
def whatsapp_feedback_webhook(payload: WhatsAppInboundMessage, db: Session = Depends(get_db)) -> Signal:
    """Consomme la reponse OUI/NON d'un entrepreneur au bouton de retour
    rapide envoye avec chaque rapport (§3.3), pour alimenter la boucle de
    correction humaine (§5.5.3)."""
    try:
        feedback = parse_feedback_message(payload.texte)
    except FeedbackParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _appliquer_feedback(db, feedback.signal_id, feedback.pertinent)
