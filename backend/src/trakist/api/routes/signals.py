import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from trakist.db import get_db
from trakist.models.signal import Signal, StatutSignal
from trakist.schemas.signal import SignalFeedback, SignalOut

router = APIRouter(tags=["signals"])


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
    signal = db.get(Signal, signal_id)
    if signal is None:
        raise HTTPException(status_code=404, detail="Signal introuvable")
    signal.statut = StatutSignal.JUGE_PERTINENT if payload.pertinent else StatutSignal.JUGE_NON_PERTINENT
    db.commit()
    db.refresh(signal)
    return signal
