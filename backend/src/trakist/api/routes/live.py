import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from trakist.db import get_db
from trakist.models.live import LiveSession, Reservation, StatutLive, Transaction
from trakist.schemas.live import (
    LiveCommentCreate,
    LiveCommentOut,
    LiveSessionCreate,
    LiveSessionOut,
    PaymentWebhookPayload,
    ReservationOut,
)
from trakist.services.reconciliation.live_service import LiveReconciliationService, ReconciliationError
from trakist.timeutils import utcnow

router = APIRouter(tags=["live"])


@router.post("/live-sessions", response_model=LiveSessionOut, status_code=201)
def start_live_session(payload: LiveSessionCreate, db: Session = Depends(get_db)) -> LiveSession:
    live_session = LiveSession(business_id=payload.business_id, channel_id=payload.channel_id)
    db.add(live_session)
    db.commit()
    db.refresh(live_session)
    return live_session


@router.post("/live-sessions/{live_session_id}/end", response_model=LiveSessionOut)
def end_live_session(live_session_id: uuid.UUID, db: Session = Depends(get_db)) -> LiveSession:
    live_session = db.get(LiveSession, live_session_id)
    if live_session is None:
        raise HTTPException(status_code=404, detail="Live session introuvable")
    live_session.statut = StatutLive.TERMINEE
    live_session.ended_at = utcnow()
    db.commit()
    db.refresh(live_session)
    return live_session


@router.post("/live-sessions/{live_session_id}/comments", response_model=LiveCommentOut, status_code=201)
def add_live_comment(
    live_session_id: uuid.UUID, payload: LiveCommentCreate, db: Session = Depends(get_db)
) -> LiveCommentOut:
    service = LiveReconciliationService(db)
    try:
        return service.ajouter_commentaire(
            live_session_id, payload.auteur, payload.texte, payload.article_ref
        )
    except ReconciliationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/live-sessions/{live_session_id}/journal", response_model=list[LiveCommentOut])
def get_live_session_journal(live_session_id: uuid.UUID, db: Session = Depends(get_db)) -> list:
    """Journal de transaction tracable en cas de litige (§3.4)."""
    live_session = db.get(LiveSession, live_session_id)
    if live_session is None:
        raise HTTPException(status_code=404, detail="Live session introuvable")
    return sorted(live_session.comments, key=lambda c: c.horodatage)


@router.post("/reservations/{reservation_id}/expirer", response_model=ReservationOut | None)
def expire_reservation(reservation_id: uuid.UUID, db: Session = Depends(get_db)):
    """A appeler par un ordonnanceur periodique (hors squelette) une fois la
    fenetre depassee ; libere automatiquement le suivant de la file."""
    service = LiveReconciliationService(db)
    try:
        return service.expirer_et_liberer(reservation_id)
    except ReconciliationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/webhooks/payments/momo", response_model=ReservationOut)
def payment_webhook(payload: PaymentWebhookPayload, db: Session = Depends(get_db)) -> Reservation:
    stmt = select(Transaction).where(Transaction.reference_externe == payload.reference_externe)
    transaction = db.execute(stmt).scalars().first()
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction inconnue pour cette reference")

    service = LiveReconciliationService(db)
    try:
        return service.confirmer_paiement(transaction.reservation_id, payload.reference_externe)
    except ReconciliationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
