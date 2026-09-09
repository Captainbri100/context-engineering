# AGENTS.md — house rules
- Orders are NEVER deleted — 7-year audit retention. "Cancel" means setting a cancelled_at timestamp on the order; the row stays.
- Every cancellation must record a reason (required string) — our audit reports depend on it.
- Cancelling an order MUST return its quantity to product stock.
- Every endpoint response uses the wrap() envelope helper in app/routes.py — never raw dicts.
