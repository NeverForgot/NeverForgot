import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from trakist.db import get_db
from trakist.models.business import Business
from trakist.schemas.business import BusinessCreate, BusinessOut

router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.post("", response_model=BusinessOut, status_code=201)
def create_business(payload: BusinessCreate, db: Session = Depends(get_db)) -> Business:
    business = Business(**payload.model_dump())
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


@router.get("/{business_id}", response_model=BusinessOut)
def get_business(business_id: uuid.UUID, db: Session = Depends(get_db)) -> Business:
    business = db.get(Business, business_id)
    if business is None:
        raise HTTPException(status_code=404, detail="Business introuvable")
    return business


@router.get("", response_model=list[BusinessOut])
def list_businesses(country_code: str | None = None, db: Session = Depends(get_db)) -> list[Business]:
    query = db.query(Business)
    if country_code:
        query = query.filter(Business.country_code == country_code)
    return query.all()
