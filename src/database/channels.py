import sqlite3
from dataclasses import dataclass

from src.shared.exceptions import (
    ChannelAlreadyExistsError,
    ChannelNotFoundError,
)
from src.shared.services import services


@dataclass
class TelegramChannel:
    channel_id: int
    username: str
    added_at: str


def _init_channel_tables() -> None:
    db = services.database

    # Create telegram_channels table
    if not db.table_exists("telegram_channels"):
        create_telegram_table = """
            CREATE TABLE telegram_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL UNIQUE,
                username TEXT NOT NULL UNIQUE,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        db.create_table_if_not_exists(create_telegram_table)


# Initialize tables on module import
_init_channel_tables()


def add_telegram_channel(channel_id: int, username: str) -> None:
    """
    Add a Telegram channel to the database.

    Args:
        channel_id: Telegram channel ID
        username: Telegram channel username

    Raises:
        ChannelAlreadyExistsError: If channel already exists
        sqlite3.DatabaseError: If database operation fails
    """
    db = services.database
    try:
        db.execute(
            "INSERT INTO telegram_channels (channel_id, username) VALUES (?, ?)",
            (channel_id, username),
        )
    except sqlite3.IntegrityError:
        raise ChannelAlreadyExistsError(
            f"Telegram channel {channel_id} ({username}) already exists"
        ) from None


def remove_telegram_channel(channel_id: int) -> None:
    """
    Remove a Telegram channel from the database.

    Args:
        channel_id: Telegram channel ID

    Raises:
        ChannelNotFoundError: If channel doesn't exist
        sqlite3.DatabaseError: If database operation fails
    """
    db = services.database
    existing = db.fetch_one(
        "SELECT id FROM telegram_channels WHERE channel_id = ?",
        (channel_id,),
    )
    if not existing:
        raise ChannelNotFoundError(f"Telegram channel {channel_id} not found")

    db.execute(
        "DELETE FROM telegram_channels WHERE channel_id = ?",
        (channel_id,),
    )


def list_telegram_channels() -> list[TelegramChannel]:
    """
    Returns:
        List of all stored Telegram channels
    """
    db = services.database
    rows = db.fetch_all(
        "SELECT channel_id, username, added_at FROM telegram_channels ORDER BY added_at DESC"
    )
    return [TelegramChannel(**dict(row)) for row in rows]
