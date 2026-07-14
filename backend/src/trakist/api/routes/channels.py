import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from trakist.db import get_db
from trakist.models.business import Business, Channel
from trakist.schemas.channel import ChannelCreate, ChannelOut

router = APIRouter(tags=["channels"])


@router.post("/businesses/{business_id}/channels", response_model=ChannelOut, status_code=201)
def connect_channel(
    business_id: uuid.UUID, payload: ChannelCreate, db: Session = Depends(get_db)
) -> Channel:
    if db.get(Business, business_id) is None:
        raise HTTPException(status_code=404, detail="Business introuvable")
    channel = Channel(business_id=business_id, **payload.model_dump())
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel


@router.get("/businesses/{business_id}/channels", response_model=list[ChannelOut])
def list_channels(business_id: uuid.UUID, db: Session = Depends(get_db)) -> list[Channel]:
    return db.query(Channel).filter(Channel.business_id == business_id).all()
