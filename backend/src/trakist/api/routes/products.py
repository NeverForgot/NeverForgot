import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from trakist.db import get_db
from trakist.models.business import Business
from trakist.models.product import Product
from trakist.schemas.product import ProductCreate, ProductOut

router = APIRouter(tags=["products"])


@router.post("/businesses/{business_id}/products", response_model=ProductOut, status_code=201)
def create_product(business_id: uuid.UUID, payload: ProductCreate, db: Session = Depends(get_db)) -> Product:
    if db.get(Business, business_id) is None:
        raise HTTPException(status_code=404, detail="Business introuvable")

    stmt = select(Product).where(Product.business_id == business_id, Product.reference == payload.reference)
    if db.execute(stmt).scalars().first() is not None:
        raise HTTPException(status_code=409, detail="Un produit existe deja avec cette reference")

    product = Product(business_id=business_id, **payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/businesses/{business_id}/products", response_model=list[ProductOut])
def list_products(business_id: uuid.UUID, db: Session = Depends(get_db)) -> list[Product]:
    return db.query(Product).filter(Product.business_id == business_id).all()
