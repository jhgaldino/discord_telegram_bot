import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker

from src.database.models import Base


class Database:
    """
    Database management class with proper SQLAlchemy session handling.

    This class provides a convenient interface for database operations
    using SQLAlchemy ORM. Tables are automatically created on initialization.
    """

    def __init__(self) -> None:
        """Initialize database connection and create tables."""
        database_url = self._get_database_url()
        self.engine = create_engine(
            database_url,
            echo=False,
            connect_args={"check_same_thread": False}
            if database_url.startswith("sqlite")
            else {},
            pool_pre_ping=True if not database_url.startswith("sqlite") else False,
        )
        self.SessionLocal = sessionmaker(
            bind=self.engine, autocommit=False, autoflush=False
        )
        # Automatically create tables on initialization
        self.create_tables()

    @staticmethod
    def _get_database_url() -> str:
        """
        Get database URL from environment variable or default to SQLite.

        Returns:
            Database URL string (e.g., 'sqlite:///database.db' or 'postgresql://...')
        """
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return database_url

        db_path = Path("database.db")
        return f"sqlite:///{db_path}"

    @contextmanager
    def get_session(self) -> Generator[Session]:
        """
        Get a database session context manager.

        Yields:
            SQLAlchemy session

        Example:
            with db.get_session() as session:
                # Use session here
                pass
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name: Name of the table to check

        Returns:
            True if table exists, False otherwise
        """
        with self.get_session() as session:
            if session.bind is None:
                return False
            inspector = inspect(session.bind)
            return table_name in inspector.get_table_names()

    def create_tables(self) -> None:
        """Create all tables defined in models."""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self) -> None:
        """Drop all tables. Use with caution!"""
        Base.metadata.drop_all(bind=self.engine)
