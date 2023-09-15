import os
from contextlib import contextmanager
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dependencies import SETTINGS


DATABASE_URL = SETTINGS.DB_URL

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