# order-desk

A small FastAPI service for a shop: products with stock, and orders that reserve it.

The four house rules this project runs on live in [`AGENTS.md`](AGENTS.md) — that
file is the whole point of the context engineering video.

## Run it

    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload

The API serves on http://localhost:8000 (interactive docs at /docs).
Three products are seeded on first startup.

## Endpoints

- `GET /products` — list products with live stock
- `GET /orders` — list orders
- `POST /orders` — place an order (reserves stock)
- `POST /orders/{id}/cancel` — cancel an order (records a reason, returns stock)

## Tests

    pytest
