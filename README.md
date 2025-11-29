````markdown
# Looplink Mini Sticker Engine

A robust backend service powering a retail loyalty campaign. This engine calculates sticker rewards from purchase transactions and enables shoppers to redeem those stickers for rewards — all while ensuring high data consistency and safe concurrent operations.

---

## 🚀 Features

### 🏅 Sticker Calculation Rules
- **Base Rule:** Earn **1 sticker** for every **$10** spent.
- **Promo Boost:** Earn **+1 sticker** for each `"Promo"` item purchased.
- **Transaction Cap:** Maximum **5 stickers per transaction**.

### 🎁 Redemption Cycle
- Shoppers can exchange stickers for rewards (e.g., **Mug**, **Tote Bag**, etc.)
- Sticker balance updates are transactional and rollback-safe.

### 🔐 Data Integrity
- **Idempotency:** Duplicate transaction submissions never grant stickers twice.
- **Atomicity:** Sticker debits & reward issuance happen inside ACID-compliant DB transactions.
- **Validation:** Strict input/output schemas using **Pydantic**.
- **Observability:** Structured logging and centralized exception flow.

---

## 🛠️ Tech Stack

| Layer        | Technology            |
|--------------|-----------------------|
| Language     | Python 3.10+          |
| Framework    | FastAPI               |
| Database     | PostgreSQL            |
| ORM          | SQLModel (SQLAlchemy + Pydantic) |

---

## 🏃‍♂️ Getting Started

### 1️⃣ Prerequisites
Ensure the following are installed:

- Python 3.10 or above
- PostgreSQL

### 2️⃣ Project Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd looplink-project

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install "fastapi[standard]" sqlmodel psycopg2-binary
````

### 3️⃣ Database Setup

Start your PostgreSQL instance, then create the DB:

```bash
createdb sticker_db
```

> 📝 Tables are auto-generated on first run.

### 4️⃣ Run the Server

```bash
fastapi dev main.py
```

Your API is now live at:

```
http://127.0.0.1:8000
```

---

## 📖 API Documentation

FastAPI automatically provides interactive API docs:

* Swagger UI → `http://127.0.0.1:8000/docs`
* ReDoc → `http://127.0.0.1:8000/redoc`

---

## 🔑 Key Endpoints

| Method | Endpoint         | Description                                |
| -----: | ---------------- | ------------------------------------------ |
|   POST | `/transactions`  | Submit purchase receipts and earn stickers |
|    GET | `/shoppers/{id}` | View shopper sticker balance & history     |
|    GET | `/rewards`       | View available rewards and sticker costs   |
|   POST | `/redemptions`   | Redeem stickers for a reward               |

---

## 🧪 Quick Test Flow

1. **Earn Stickers**
   Submit a transaction of **$50** → Shopper earns **5 stickers**

2. **Redeem**
   Redeem reward: `STICKER_PACK` (cost: 5)

3. **Verify**
   Check balance → should now be **0**

---


```

Here is a polished version you can paste directly into your `README.md` — concise, clear, and professional:

---

## 🧪 Running Tests

This project includes automated tests covering:

* **Core business logic** — sticker calculation rules and edge cases
* **System guarantees** — idempotent transaction processing

### 1️⃣ Install Test Dependencies

```bash
pip install pytest httpx
```

### 2️⃣ Execute the Test Suite

```bash
pytest
```

### ✅ Expected Output

```
test_app.py ..                                                     [100%]
2 passed in 0.15s
```

