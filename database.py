from sqlmodel import SQLModel, create_engine, Session

# 1. Connection String
# On Mac, the default user is usually your system username, and there is no password.
# We connect to localhost and the 'sticker_db' we created earlier.
DATABASE_URL = "postgresql://localhost/sticker_db"

# 2. The Engine (The Connection Factory)
# echo=True means "Print all SQL commands to the terminal" (Debug mode)
engine = create_engine(DATABASE_URL, echo=True)

# 3. Create Tables Function
# We call this to create the tables (Shopper, Transaction, Item) in the DB
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# 4. Session Dependency
# This allows the API to borrow a connection and automatically close it later.
def get_session():
    with Session(engine) as session:
        yield session