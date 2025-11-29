```markdown
# TECH_NOTES.md — Technical Implementation Notes

This document explains **why** the solution is designed the way it is. It outlines the architectural choices, trade-offs, and how to manually verify key features of the system.

---

## 1. Architectural Decisions

### 🧱 A. Modular Design & Separation of Responsibilities

To keep the codebase maintainable and testable, the system is split into clear layers:

| File | Responsibility |
|------|---------------|
| **`models.py`** | Defines domain models and database schema |
| **`schemas.py`** | Pydantic DTOs for request/response validation; isolates API contract from DB internals |
| **`services.py`** | Core business logic (sticker calculation, bonus rules, transaction caps) |
| **`database.py`** | Database connectivity, session lifecycle, and engine configuration |

This separation allows:

- Independent testing of business rules  
- Safer refactoring in the future  
- Cleaner HTTP endpoints that don’t mix DB logic with calculations  

---

### 💰 B. Data Accuracy & Consistency

- **Decimal Instead of Float**  
  All monetary values use `Decimal` to avoid floating-point precision issues during calculations such as:
```

19.99 + 0.01 != 20.00  # with floats

````

- **Atomic Database Writes**  
Sticker calculation and transaction persistence occur within a **single DB session**, guaranteeing consistency even under retry scenarios.

---

### 🔁 C. Idempotency & Concurrency Reliability

- **Idempotent Transactions**  
`transaction_id` is used as the **Primary Key** in the database.  
If the same transaction is processed twice:

- Same payload → returned from DB without double-awarding stickers  
- Conflicting payload → rejected  

- **Database-backed Guarantees**  
Relying on ACID constraints ensures that even concurrent requests cannot insert duplicate transactions.

- **Connection Pooling**  
SQLAlchemy’s engine provides efficient pooling for concurrent workloads.

---

## 2. Trade-offs: MVP vs Production

| Concern | MVP Decision | Production-ready Approach |
|--------|-------------|--------------------------|
| Sticker awarding | Done synchronously | Move to an **Async Job Queue** such as Celery, Kafka, or RabbitMQ |
| Timezones | Stored “as received” | Strict UTC enforcement and timezone normalization |
| Scaling | Best-effort concurrency | Horizontal scaling + DB sharding or CQRS if needed |

The current solution optimizes for **clarity and correctness**, not for maximum throughput.

---

## 3. Manual Testing Guide

You can manually verify the entire reward flow using `curl`.

---

### 🛒 Step 1 — Earn Stickers by Submitting a Transaction

```bash
curl -X POST http://127.0.0.1:8000/transactions \
-H "Content-Type: application/json" \
-d '{
  "transaction_id": "tx-demo-01",
  "shopper_id": "shopper-demo",
  "store_id": "store-01",
  "timestamp": "2025-11-29T10:00:00Z",
  "items": [
    {"sku": "MILK", "name": "Milk", "quantity": 2, "unit_price": 5, "category": "grocery"},
    {"sku": "TOY", "name": "Promo Toy", "quantity": 1, "unit_price": 15, "category": "promo"}
  ]
}'
````

**Expected outcome:**
Basket total = `2×5 + 1×15 = 25` → **3 stickers earned**

---

### 🧾 Step 2 — Retrieve Sticker Balance

```bash
curl http://127.0.0.1:8000/shoppers/shopper-demo
```

You should now see `3` stickers in the response.

---

### 🎁 Step 3 — Redeem Stickers

```bash
curl -X POST http://127.0.0.1:8000/redemptions \
  -H "Content-Type: application/json" \
  -d '{
    "redemption_id": "red-demo-01",
    "shopper_id": "shopper-demo",
    "reward_code": "MUG"
  }'
```

If the shopper has enough stickers, the reward is granted and stickers are deducted.

---

## 4. AI Usage Statement

AI tools were used **as a productivity assistant**, not as an autonomous author.
Specifically, AI helped with:

* Generating boilerplate Pydantic and FastAPI structures
* Optimizing folder organization to industry conventions
* Producing curl examples for manual testing

However:

> **Every line of code was reviewed, understood, and validated by me.**
> No unreviewed or blindly generated code was committed.

---


