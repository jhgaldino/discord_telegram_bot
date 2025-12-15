"""Reminder management functions using the Database class."""

import sqlite3

from src.database import get_database


def _init_reminders_table() -> None:
    """Initialize the reminders table if it doesn't exist."""
    db = get_database()
    if not db.table_exists("reminders"):
        create_table_query = """
            CREATE TABLE reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                reminder TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, reminder)
            )
        """
        db.create_table_if_not_exists(create_table_query)


# Initialize table on module import
_init_reminders_table()


def add_reminder(user_id: int, reminder: str) -> None:
    """
    Add a reminder for a user.

    Args:
        user_id: Discord user ID
        reminder: Reminder text to add
    """
    db = get_database()
    try:
        insert_query = """
            INSERT INTO reminders (user_id, reminder) VALUES (?, LOWER(?))
        """
        db.execute(insert_query, (user_id, reminder))
    except sqlite3.IntegrityError:
        # Ignore duplicate reminder error
        pass


def get_user_reminders(user_id: int) -> list[str]:
    """
    Get all reminders for a user.

    Args:
        user_id: Discord user ID

    Returns:
        List of reminder texts for the user
    """
    db = get_database()
    select_query = """
        SELECT reminder FROM reminders
        WHERE user_id = ?
        ORDER BY created_at DESC
    """
    results = db.fetch_all(select_query, (user_id,))
    return [row["reminder"] for row in results]


def remove_reminder(user_id: int, reminder: str) -> None:
    """
    Remove a reminder for a user.

    Args:
        user_id: Discord user ID
        reminder: Reminder text to remove
    """
    db = get_database()
    delete_query = """
        DELETE FROM reminders
        WHERE user_id = ? AND reminder = LOWER(?)
    """
    db.execute(delete_query, (user_id, reminder))


def get_all_reminders() -> list[str]:
    """
    Get all unique reminders across all users.

    Returns:
        List of all unique reminder texts
    """
    db = get_database()
    select_query = """
        SELECT reminder FROM reminders
        GROUP BY reminder
    """
    results = db.fetch_all(select_query)
    return [row["reminder"] for row in results]


def find_matching_reminders(text: str) -> dict[int, list[str]]:
    """
    Find users whose reminders match the given text.

    Args:
        text: Text to search for reminders in

    Returns:
        Dictionary mapping user IDs to lists of matching reminder texts
    """
    db = get_database()
    select_query = """
        SELECT user_id, reminder FROM reminders
        WHERE INSTR(LOWER(?), LOWER(reminder)) > 0
    """
    results = db.fetch_all(select_query, (text,))

    reminder_by_user: dict[int, list[str]] = {}
    for row in results:
        user_id = row["user_id"]
        reminder = row["reminder"]
        if user_id not in reminder_by_user:
            reminder_by_user[user_id] = []
        reminder_by_user[user_id].append(reminder)

    return reminder_by_user
