from decimal import Decimal
from typing import List
from models import Item

def calculate_stickers(basket_total: Decimal, items: List[Item]) -> int:
    """
    Calculates the number of stickers earned for a transaction.
    
    Rules:
    1. Base: 1 sticker per $10 spent (floored).
    2. Bonus: +1 sticker for every item with category 'promo'.
    3. Cap: Max 5 stickers total per transaction.
    """
    
    # Rule 1: Base Earn Rate (1 per $10)
    # convert 25.50 -> 2.55 -> int(2)
    base_stickers = int(basket_total // 10)
    
    # Rule 2: Promo Item Bonus
    # We count how many items have the category "promo"
    promo_bonus = 0
    for item in items:
        if item.category == "promo":
            # We add 1 sticker for EACH promo unit (quantity * 1)
            promo_bonus += item.quantity
            
    # Calculate raw total
    total = base_stickers + promo_bonus
    
    # Rule 3: Per-transaction cap
    # If total is 8, return 5. If total is 3, return 3.
    final_stickers = min(total, 5)
    
    return final_stickers