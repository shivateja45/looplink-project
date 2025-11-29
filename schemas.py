from pydantic import BaseModel
from typing import List
from decimal import Decimal
from datetime import datetime

# -----------------------------------------------------------------------------
# INPUT SCHEMAS (What the user sends us)
# -----------------------------------------------------------------------------

class ItemCreate(BaseModel):
    """
    Represents an item in the shopping basket during a request.
    We don't need 'transaction_id' here because it hasn't been created yet.
    """
    sku: str
    name: str
    category: str
    quantity: int
    unit_price: Decimal

class TransactionCreate(BaseModel):
    """
    The payload for creating a new transaction.
    Notice: No 'stickers_awarded' field. The user cannot set that!
    """
    transaction_id: str
    shopper_id: str
    store_id: str
    timestamp: datetime
    items: List[ItemCreate]


# -----------------------------------------------------------------------------
# OUTPUT SCHEMAS (What we send back)
# -----------------------------------------------------------------------------

class TransactionResponse(BaseModel):
    """
    What we return after processing.
    Now we include the calculated fields.
    """
    transaction_id: str
    shopper_id: str
    store_id: str
    basket_total: Decimal
    stickers_awarded: int
    shopper_sticker_balance: int  

class RedemptionRequest(BaseModel):
    redemption_id: str
    shopper_id: str
    reward_code: str

class RedemptionResponse(BaseModel):
    redemption_id: str
    shopper_id: str
    reward_code: str
    stickers_spent: int
    shopper_sticker_balance: int 