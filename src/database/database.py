"""Database management with proper connection handling."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator


class Database:
    """Database management class with proper connection handling."""

    def __init__(self, db_path: str | Path = "database.db") -> None:
        """
        Initialize the database.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self._ensure_database_dir()

    def _ensure_database_dir(self) -> None:
        """Ensure the database directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get a database connection as a context manager.

        Yields:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def execute(self, query: str, params: tuple = ()) -> None:
        """
        Execute a query that modifies the database.

        Args:
            query: SQL query to execute
            params: Query parameters
        """
        with self.get_connection() as conn:
            conn.execute(query, params)
            conn.commit()

    def fetch_all(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        """
        Execute a SELECT query and return all results.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            List of rows from the query
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    def fetch_one(self, query: str, params: tuple = ()) -> sqlite3.Row | None:
        """
        Execute a SELECT query and return one result.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            Single row from the query, or None if no results
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name: Name of the table to check

        Returns:
            True if table exists, False otherwise
        """
        query = """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        """
        result = self.fetch_one(query, (table_name,))
        return result is not None

    def create_table_if_not_exists(self, query: str) -> None:
        """
        Create a table if it doesn't exist.

        Args:
            query: CREATE TABLE query
        """
        self.execute(query)
