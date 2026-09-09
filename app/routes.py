from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import models, schemas
from .database import get_db

router = APIRouter()


def wrap(data):
    """Standard response envelope used by every endpoint."""
    return {"data": data, "error": None}


@router.get("/products")
def list_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).order_by(models.Product.name).all()
    return wrap([schemas.ProductOut.model_validate(p).model_dump() for p in products])


@router.get("/orders")
def list_orders(db: Session = Depends(get_db)):
    orders = db.query(models.Order).order_by(models.Order.created_at).all()
    return wrap([schemas.OrderOut.model_validate(o).model_dump(mode="json") for o in orders])


@router.post("/orders", status_code=201)
def create_order(payload: schemas.OrderCreate, db: Session = Depends(get_db)):
    product = db.get(models.Product, payload.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock < payload.quantity:
        raise HTTPException(status_code=409, detail="Insufficient stock")

    product.stock -= payload.quantity
    order = models.Order(
        product_id=product.id,
        quantity=payload.quantity,
        total_cents=product.price_cents * payload.quantity,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return wrap(schemas.OrderOut.model_validate(order).model_dump(mode="json"))


@router.post("/orders/{order_id}/cancel")
def cancel_order(order_id: int, payload: schemas.OrderCancel, db: Session = Depends(get_db)):
    order = db.get(models.Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.cancelled_at is not None:
        raise HTTPException(status_code=409, detail="Order already cancelled")

    order.cancelled_at = datetime.now(timezone.utc)
    order.cancel_reason = payload.reason
    order.product.stock += order.quantity
    db.commit()
    db.refresh(order)
    return wrap(schemas.OrderOut.model_validate(order).model_dump(mode="json"))
