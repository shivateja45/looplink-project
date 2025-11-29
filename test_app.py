import uuid
from fastapi.testclient import TestClient
from decimal import Decimal
from main import app
from services import calculate_stickers
from models import Item

client = TestClient(app)

# Helper to get a unique ID string
def get_id():
    return str(uuid.uuid4())

# -----------------------------------------------------------------------------
# 1. LOGIC TESTS
# -----------------------------------------------------------------------------
def test_sticker_calculation_logic():
    items = [
        Item(sku="A", name="Milk", category="grocery", quantity=2, unit_price=Decimal("5.00")), # $10
        Item(sku="B", name="Toy", category="promo", quantity=1, unit_price=Decimal("15.00"))   # $15
    ]
    assert calculate_stickers(Decimal("25.00"), items) == 3

def test_calculation_zero_promo_quantity():
    items = [
        Item(sku="B", name="Toy", category="promo", quantity=0, unit_price=Decimal("15.00"))
    ]
    assert calculate_stickers(Decimal("0.00"), items) == 0

# -----------------------------------------------------------------------------
# 2. VALIDATION TESTS
# -----------------------------------------------------------------------------
def test_reject_negative_values():
    payload = {
        "transaction_id": get_id(),
        "shopper_id": f"shopper-{get_id()}", # Randomize shopper
        "store_id": "store-1",
        "timestamp": "2025-01-01T10:00:00Z",
        "items": [
            {"sku": "A", "name": "Bad", "category": "grocery", "quantity": -5, "unit_price": 10.00}
        ]
    }
    response = client.post("/transactions", json=payload)
    assert response.status_code == 422

# -----------------------------------------------------------------------------
# 3. TRANSACTION TESTS
# -----------------------------------------------------------------------------
def test_duplicate_transaction_idempotency():
    # Use a unique Transaction ID AND unique Shopper ID
    tx_id = get_id()
    shopper_id = f"shopper-{get_id()}"
    
    payload = {
        "transaction_id": tx_id,
        "shopper_id": shopper_id,
        "store_id": "store-1",
        "timestamp": "2025-01-01T10:00:00Z",
        "items": [
            {"sku": "A", "name": "A", "category": "grocery", "quantity": 1, "unit_price": 50.00}
        ]
    }
    # First -> 201 Created (Balance 0 -> 5)
    r1 = client.post("/transactions", json=payload)
    assert r1.status_code == 201
    assert r1.json()["shopper_sticker_balance"] == 5

    # Second -> 201 Created (Balance Should Stay 5)
    r2 = client.post("/transactions", json=payload)
    assert r2.status_code == 201
    assert r2.json()["shopper_sticker_balance"] == 5

# -----------------------------------------------------------------------------
# 4. REDEMPTION TESTS
# -----------------------------------------------------------------------------
def test_redemption_flow():
    # Generate unique IDs for this test run so we don't clash with DB
    shopper_id = f"shopper-{get_id()}"
    
    setup_payload = {
        "store_id": "store-1",
        "shopper_id": shopper_id,
        "timestamp": "2025-01-01T10:00:00Z",
        "items": [
            {"sku": "A", "name": "A", "category": "grocery", "quantity": 3, "unit_price": 50.00} 
        ]
    }
    
    # Run 3 times to get 15 stickers (5 per transaction cap)
    client.post("/transactions", json={**setup_payload, "transaction_id": get_id()})
    client.post("/transactions", json={**setup_payload, "transaction_id": get_id()})
    client.post("/transactions", json={**setup_payload, "transaction_id": get_id()})
    
    # Check Balance is 15
    r_check = client.get(f"/shoppers/{shopper_id}")
    assert r_check.json()["sticker_balance"] == 15

    # 2. Redeem MUG (Cost 10)
    redemption_id = get_id()
    redemption_payload = {
        "redemption_id": redemption_id,
        "shopper_id": shopper_id,
        "reward_code": "MUG"
    }
    r_redeem = client.post("/redemptions", json=redemption_payload)
    assert r_redeem.status_code == 201
    assert r_redeem.json()["stickers_spent"] == 10
    assert r_redeem.json()["shopper_sticker_balance"] == 5 

    # 3. Fail TOTE (Cost 20)
    redemption_fail = {
        "redemption_id": get_id(),
        "shopper_id": shopper_id,
        "reward_code": "TOTE"
    }
    r_fail = client.post("/redemptions", json=redemption_fail)
    assert r_fail.status_code == 400

    # 4. Idempotency (Replay the MUG redemption)
    r_replay = client.post("/redemptions", json=redemption_payload)
    assert r_replay.status_code == 201
    assert r_replay.json()["shopper_sticker_balance"] == 5