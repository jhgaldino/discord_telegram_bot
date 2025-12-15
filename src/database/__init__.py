"""Database package - Database management and related functionality."""

from src.database.database import Database

# Global database instance
_db_instance: Database | None = None


def get_database() -> Database:
    """
    Get the global database instance.

    Returns:
        Database instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


# Expose public API
__all__ = ["Database", "get_database"]
