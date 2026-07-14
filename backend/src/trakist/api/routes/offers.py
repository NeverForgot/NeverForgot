import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from trakist.db import get_db
from trakist.models.business import Business, Offer
from trakist.schemas.offer import OfferCreate, OfferOut

router = APIRouter(tags=["offers"])


@router.post("/businesses/{business_id}/offers", response_model=OfferOut, status_code=201)
def create_offer(business_id: uuid.UUID, payload: OfferCreate, db: Session = Depends(get_db)) -> Offer:
    if db.get(Business, business_id) is None:
        raise HTTPException(status_code=404, detail="Business introuvable")
    offer = Offer(business_id=business_id, **payload.model_dump())
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


@router.get("/businesses/{business_id}/offers", response_model=list[OfferOut])
def list_offers(business_id: uuid.UUID, db: Session = Depends(get_db)) -> list[Offer]:
    return db.query(Offer).filter(Offer.business_id == business_id).all()
