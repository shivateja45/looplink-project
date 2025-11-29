from fastapi.testclient import TestClient
from decimal import Decimal
from main import app
from services import calculate_stickers
from models import Item

# Create a "Fake Browser" client to talk to our API
client = TestClient(app)

# -----------------------------------------------------------------------------
# 1. UNIT TEST: Pure Logic (No Database)
# -----------------------------------------------------------------------------
def test_sticker_calculation_logic():
    """
    Test the math rules in isolation.
    """
    # Case A: $25 spend (2.5 -> 2 stickers) + 1 Promo
    items = [
        Item(sku="A", name="Milk", category="grocery", quantity=2, unit_price=Decimal("5.00")), # $10
        Item(sku="B", name="Toy", category="promo", quantity=1, unit_price=Decimal("15.00"))   # $15
    ]
    # Total $25. Base = 2. Promo = 1. Total = 3.
    result = calculate_stickers(Decimal("25.00"), items)
    assert result == 3

    # Case B: The CAP Rule ($1000 spend -> should be capped at 5)
    items_huge = [
        Item(sku="C", name="TV", category="electronics", quantity=1, unit_price=Decimal("1000.00"))
    ]
    result_huge = calculate_stickers(Decimal("1000.00"), items_huge)
    assert result_huge == 5

# -----------------------------------------------------------------------------
# 2. INTEGRATION TEST: Idempotency (Database Safety)
# -----------------------------------------------------------------------------
def test_duplicate_transaction_idempotency():
    """
    If we send the same transaction ID twice, the balance should not increase twice.
    """
    payload = {
        "transaction_id": "test-tx-duplicate-1",
        "shopper_id": "test-shopper-1",
        "store_id": "store-1",
        "timestamp": "2025-01-01T10:00:00Z",
        "items": [
            {"sku": "A", "name": "A", "category": "grocery", "quantity": 1, "unit_price": 50.00} # $50 -> 5 stickers
        ]
    }

    # Attempt 1: Should create (201 Created)
    response1 = client.post("/transactions", json=payload)
    assert response1.status_code == 201
    assert response1.json()["stickers_awarded"] == 5
    assert response1.json()["shopper_sticker_balance"] == 5

    # Attempt 2: Should return existing (201 Created or 200 OK)
    # BUT balance must NOT change
    response2 = client.post("/transactions", json=payload)
    assert response2.status_code == 201
    assert response2.json()["stickers_awarded"] == 5
    # Critical Check: Balance should still be 5, NOT 10
    assert response2.json()["shopper_sticker_balance"] == 5