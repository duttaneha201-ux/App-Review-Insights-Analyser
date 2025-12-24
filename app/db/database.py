"""
Database connection and session management
"""

import os
from pathlib import Path
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator

# Default database path
DEFAULT_DB_PATH = Path("data/reviews.db")
DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Database URL
DB_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.absolute()}")

# For in-memory testing
TEST_DB_URL = "sqlite:///:memory:"

# Create engine
# Use StaticPool for SQLite to allow multiple threads/connections
connect_args = {}
if "sqlite" in DB_URL:
    connect_args["check_same_thread"] = False

engine = create_engine(
    DB_URL,
    connect_args=connect_args,
    poolclass=StaticPool if "sqlite" in DB_URL else None,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
)

# Enable foreign key constraints for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    if "sqlite" in DB_URL:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Get a database session (dependency injection pattern).
    
    Usage:
        with get_db_session() as session:
            # use session
            pass
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    """
    Initialize database by creating all tables.
    Call this after running migrations or for testing.
    """
    from app.db.models import Base
    
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_test_db_session() -> Generator[Session, None, None]:
    """
    Get a test database session (in-memory SQLite).
    """
    test_engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Enable foreign key constraints for test database
    @event.listens_for(test_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    from app.db.models import Base
    Base.metadata.create_all(bind=test_engine)
    
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        test_engine.dispose()

