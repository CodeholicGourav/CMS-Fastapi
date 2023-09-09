import os
from contextlib import contextmanager
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DB_URL")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# @contextmanager
def get_db():
    """
    Returns a database session object.
    
    Example Usage:
    with get_db() as db:
        # perform database operations using the db session
        ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()