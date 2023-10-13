# -*- coding: utf-8 -*-
"""
database.py - Database Configuration and ORM Setup

This module provides configuration and setup for the SQLAlchemy ORM (Object-Relational Mapping)
to interact with the database. It defines the database models, tables, and establishes the
database connection.

Classes:
    - Base: The base class for declarative ORM models.
    - Session: A utility for managing database sessions.
    - initialize_database: Function to initialize the database connection and create tables.
    - get_db: FastAPI dependency function to provide a database session to route handlers.

Usage:
    1. Import `Base` and define your database models by subclassing it.
    2. Import `Session` to manage database sessions in your application.
    3. Call `initialize_database()` to establish a database connection and create tables.
    4. Use the `get_db` function as a FastAPI dependency to access the database session in routes.

Example:
    ```python
    from sqlalchemy import Column, Integer, String
    from .database import Base

    class User(Base):
        __tablename__ = 'users'

        id = Column(Integer, primary_key=True, index=True)
        username = Column(String, unique=True, index=True)
        email = Column(String, unique=True, index=True)
    ```

    For complete usage details, refer to the README or documentation.

Author: Gourav Sahu
Date: 20/08/2023

"""

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
    databse = SessionLocal()
    try:
        yield databse
    finally:
        databse.close()
