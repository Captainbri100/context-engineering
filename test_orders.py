import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app import models

test_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
engine = create_engine(
    f"sqlite:///{test_db.name}", connect_args={"check_same_thread": False}
)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    db.add(models.Product(name="Camp Mug", price_cents=1499, stock=10))
    db.commit()
    db.close()
    yield


client = TestClient(app)


def test_create_order_reserves_stock():
    resp = client.post("/orders", json={"product_id": 1, "quantity": 3})
    assert resp.status_code == 201
    body = resp.json()
    assert body["error"] is None
    assert body["data"]["total_cents"] == 3 * 1499
    products = client.get("/products").json()["data"]
    assert products[0]["stock"] == 7


def test_insufficient_stock_rejected():
    resp = client.post("/orders", json={"product_id": 1, "quantity": 99})
    assert resp.status_code == 409


def test_unknown_product_rejected():
    resp = client.post("/orders", json={"product_id": 42, "quantity": 1})
    assert resp.status_code == 404


def test_list_orders_enveloped():
    client.post("/orders", json={"product_id": 1, "quantity": 1})
    body = client.get("/orders").json()
    assert body["error"] is None
    assert len(body["data"]) == 1


# --- cancellation ---

def test_cancel_order_restores_stock():
    order_id = client.post("/orders", json={"product_id": 1, "quantity": 4}).json()["data"]["id"]
    resp = client.post(f"/orders/{order_id}/cancel", json={"reason": "changed mind"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["error"] is None
    assert body["data"]["cancelled_at"] is not None
    assert body["data"]["cancel_reason"] == "changed mind"
    # stock should be fully restored
    stock = client.get("/products").json()["data"][0]["stock"]
    assert stock == 10


def test_cancel_already_cancelled_order_returns_409():
    order_id = client.post("/orders", json={"product_id": 1, "quantity": 1}).json()["data"]["id"]
    client.post(f"/orders/{order_id}/cancel", json={"reason": "first"})
    resp = client.post(f"/orders/{order_id}/cancel", json={"reason": "second"})
    assert resp.status_code == 409


def test_cancel_unknown_order_returns_404():
    resp = client.post("/orders/9999/cancel", json={"reason": "does not exist"})
    assert resp.status_code == 404


def test_cancel_requires_reason():
    order_id = client.post("/orders", json={"product_id": 1, "quantity": 1}).json()["data"]["id"]
    resp = client.post(f"/orders/{order_id}/cancel", json={"reason": ""})
    assert resp.status_code == 422
