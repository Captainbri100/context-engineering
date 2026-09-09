from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price_cents: int
    stock: int


class OrderCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderCancel(BaseModel):
    reason: str = Field(min_length=1)


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    total_cents: int
    created_at: datetime
    cancelled_at: datetime | None = None
    cancel_reason: str | None = None
