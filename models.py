from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship

class Shopper(SQLModel, table=True):
    """
    Represents a customer in the loyalty system.
    
    Key Decisions:
    - sticker_balance is stored here for O(1) access (fast reads),
      rather than recalculating it from transaction history every time.
    """
    shopper_id: str = Field(primary_key=True)
    sticker_balance: int = Field(default=0)
    
    # Relationship: One Shopper has many Transactions
    transactions: List["Transaction"] = Relationship(back_populates="shopper")


class Transaction(SQLModel, table=True):
    """
    Represents a single purchase receipt.
    
    Key Decisions:
    - transaction_id is unique to ensure Idempotency (preventing double-counts).
    - basket_total uses Decimal (not Float) to avoid floating-point money errors.
    """
    transaction_id: str = Field(primary_key=True)
    shopper_id: str = Field(foreign_key="shopper.shopper_id", index=True)
    store_id: str
    timestamp: datetime
    
    # max_digits=10, decimal_places=2 handles amounts up to 99,999,999.99
    basket_total: Decimal = Field(default=0, max_digits=10, decimal_places=2)
    
    stickers_awarded: int = Field(default=0)

    shopper: Optional[Shopper] = Relationship(back_populates="transactions")
    items: List["Item"] = Relationship(back_populates="transaction")


class Item(SQLModel, table=True):
    """
    A single line item within a transaction.
    Separated into its own table to allow future analytics on specific product categories.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    transaction_id: str = Field(foreign_key="transaction.transaction_id")
    
    sku: str
    name: str
    category: str
    quantity: int
    unit_price: Decimal = Field(max_digits=10, decimal_places=2)

    transaction: Optional[Transaction] = Relationship(back_populates="items")