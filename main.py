import logging  # <--- NEW: Python's logging tool
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from typing import List

# Import our modules
from database import create_db_and_tables, get_session
from models import Transaction, Shopper, Item, Redemption
from schemas import TransactionCreate, TransactionResponse, ItemCreate, RedemptionRequest, RedemptionResponse
from services import calculate_stickers

# The Hardcoded Price List
REWARD_OPTIONS = {
    "MUG": 10,
    "TOTE": 20,
    "HOODIE": 50,
    "STICKER_PACK": 5,
    "FERARI": 10000
}

# -----------------------------------------------------------------------------
# 1. SETUP LOGGING (The "Black Box" Recorder)
# -----------------------------------------------------------------------------
# This tells Python: "Print everything INFO level and above to the terminal"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Looplink Sticker Engine")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    logger.info("✅ Application Startup: Database tables checked.")

# -----------------------------------------------------------------------------
# 2. THE SECURITY CAMERA (Validation Exception Handler)
#    This function runs whenever Pydantic rejects bad input.
# -----------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler to return clean, human-readable error messages.
    """
    # 1. Create a clean list of errors
    clean_errors = []
    
    for error in exc.errors():
        # 'loc' is a path like ('body', 'items', 0, 'price')
        # We skip the first part ('body') and join the rest with arrows
        # Example result: "items -> 0 -> price"
        field_path = " -> ".join([str(x) for x in error['loc'][1:]])
        
        # Get the simple message (e.g., "Field required" or "value is not a valid integer")
        message = error['msg']
        
        # Combine them
        clean_errors.append(f"Field '{field_path}': {message}")

    # 2. Log the clean errors (so you can read them easily in the terminal)
    logger.error(f"❌ VALIDATION FAILED at {request.url}")
    logger.error(f"   Issues: {clean_errors}")
    
    # 3. Send the clean list to the user
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "message": "Validation failed",
            "errors": clean_errors
        },
    )
# -----------------------------------------------------------------------------
# ENDPOINT 1: Ingest Transaction
# -----------------------------------------------------------------------------
@app.post("/transactions", response_model=TransactionResponse, status_code=201)
def create_transaction(
    transaction_in: TransactionCreate, 
    session: Session = Depends(get_session)
):
    # Log the attempt
    logger.info(f"📥 Processing Transaction: {transaction_in.transaction_id} for {transaction_in.shopper_id}")

    # A. Idempotency Check
    existing_tx = session.get(Transaction, transaction_in.transaction_id)
    if existing_tx:
        logger.warning(f"⚠️ Duplicate Transaction detected: {transaction_in.transaction_id}. Returning existing.")
        return TransactionResponse(
            transaction_id=existing_tx.transaction_id,
            shopper_id=existing_tx.shopper_id,
            store_id=existing_tx.store_id,
            basket_total=existing_tx.basket_total,
            stickers_awarded=existing_tx.stickers_awarded,
            shopper_sticker_balance=existing_tx.shopper.sticker_balance
        )

    # B. Calculate
    basket_total = sum(item.unit_price * item.quantity for item in transaction_in.items)
    stickers_earned = calculate_stickers(basket_total, transaction_in.items)

    # C. Handle Shopper
    shopper = session.get(Shopper, transaction_in.shopper_id)
    if not shopper:
        logger.info(f"   New Shopper detected: {transaction_in.shopper_id}")
        shopper = Shopper(shopper_id=transaction_in.shopper_id, sticker_balance=0)
        session.add(shopper)
    
    shopper.sticker_balance += stickers_earned
    session.add(shopper)

    # D. Save Transaction
    db_transaction = Transaction(
        transaction_id=transaction_in.transaction_id,
        shopper_id=transaction_in.shopper_id,
        store_id=transaction_in.store_id,
        timestamp=transaction_in.timestamp,
        basket_total=basket_total,
        stickers_awarded=stickers_earned
    )
    session.add(db_transaction)

    # E. Save Items
    for item_in in transaction_in.items:
        db_item = Item(
            transaction_id=transaction_in.transaction_id,
            sku=item_in.sku,
            name=item_in.name,
            category=item_in.category,
            quantity=item_in.quantity,
            unit_price=item_in.unit_price
        )
        session.add(db_item)

    try:
        session.commit()
        session.refresh(db_transaction)
        logger.info(f"✅ Success: Awarded {stickers_earned} stickers. New Balance: {shopper.sticker_balance}")
    except Exception as e:
        logger.error(f"❌ DATABASE ERROR: {e}")
        raise HTTPException(status_code=500, detail="Database commit failed")

    return TransactionResponse(
        transaction_id=db_transaction.transaction_id,
        shopper_id=db_transaction.shopper_id,
        store_id=db_transaction.store_id,
        basket_total=db_transaction.basket_total,
        stickers_awarded=db_transaction.stickers_awarded,
        shopper_sticker_balance=shopper.sticker_balance
    )

# -----------------------------------------------------------------------------
# ENDPOINT 2: Get Shopper Status
# -----------------------------------------------------------------------------
@app.get("/shoppers/{shopper_id}")
def get_shopper(shopper_id: str, session: Session = Depends(get_session)):
    logger.info(f"🔍 Fetching data for Shopper: {shopper_id}")
    
    shopper = session.get(Shopper, shopper_id)
    if not shopper:
        logger.warning(f"❌ Shopper not found: {shopper_id}")
        raise HTTPException(status_code=404, detail="Shopper not found")
    
    return {
        "shopper_id": shopper.shopper_id,
        "sticker_balance": shopper.sticker_balance,
        "transactions": shopper.transactions
    }

    