"""
LoreForge - Database Engine and Session Configuration
Establishes the SQLAlchemy engine using Psycopg 3 and provides session dependencies.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load local environment variables if executing outside container context
load_dotenv()

# Explicitly use the modern Psycopg 3 driver in the connection URI
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://loreforge_user:loreforge_secret@db:5432/loreforge_db"
)

# Initialize the SQLAlchemy Engine
# pool_pre_ping verifies connection vitality before queries execute
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# Factory configured for per-request database transactions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Declarative base class for ORM entity mapping
Base = declarative_base()


def get_db():
    """
    FastAPI dependency yielding an isolated database session per request.
    Closes the session cleanly upon response completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()