from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import models
from .database import Base, SessionLocal, engine
from .routes import router

SEED_PRODUCTS = [
    {"name": "Lasso Rope 30ft", "price_cents": 4599, "stock": 12},
    {"name": "Leather Work Gloves", "price_cents": 2250, "stock": 30},
    {"name": "Enamel Camp Mug", "price_cents": 1499, "stock": 50},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(models.Product).count() == 0:
            for p in SEED_PRODUCTS:
                db.add(models.Product(**p))
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(title="Order Desk", lifespan=lifespan)
app.include_router(router)
