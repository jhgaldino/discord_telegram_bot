import sqlite3
from dataclasses import dataclass

from src.shared.exceptions import (
    ChannelAlreadyExistsError,
    ChannelNotFoundError,
)
from src.shared.services import services


@dataclass
class DiscordChannel:
    channel_id: int
    added_at: str


@dataclass
class TelegramChannel:
    channel_id: int
    username: str
    added_at: str
    forward: bool


def _init_channel_tables() -> None:
    db = services.database

    # Create discord_channels table
    if not db.table_exists("discord_channels"):
        create_discord_table = """
            CREATE TABLE discord_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL UNIQUE,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        db.create_table_if_not_exists(create_discord_table)

    # Create telegram_channels table
    if not db.table_exists("telegram_channels"):
        create_telegram_table = """
            CREATE TABLE telegram_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL UNIQUE,
                username TEXT NOT NULL UNIQUE,
                forward BOOLEAN DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        db.create_table_if_not_exists(create_telegram_table)


# Initialize tables on module import
_init_channel_tables()


def add_discord_channel(channel_id: int) -> None:
    """
    Add a Discord channel to the database.

    Args:
        channel_id: Discord channel ID

    Raises:
        ChannelAlreadyExistsError: If channel already exists
        sqlite3.DatabaseError: If database operation fails
    """
    db = services.database
    try:
        db.execute(
            "INSERT INTO discord_channels (channel_id) VALUES (?)",
            (channel_id,),
        )
    except sqlite3.IntegrityError:
        raise ChannelAlreadyExistsError(
            f"Discord channel {channel_id} already exists"
        ) from None


def remove_discord_channel(channel_id: int) -> None:
    """
    Remove a Discord channel from the database.

    Args:
        channel_id: Discord channel ID

    Raises:
        ChannelNotFoundError: If channel doesn't exist
        sqlite3.DatabaseError: If database operation fails
    """
    db = services.database
    existing = db.fetch_one(
        "SELECT id FROM discord_channels WHERE channel_id = ?",
        (channel_id,),
    )
    if not existing:
        raise ChannelNotFoundError(f"Discord channel {channel_id} not found")

    db.execute("DELETE FROM discord_channels WHERE channel_id = ?", (channel_id,))


def list_discord_channels() -> list[DiscordChannel]:
    """
    Returns:
        List of all stored Discord channels
    """
    db = services.database
    rows = db.fetch_all(
        "SELECT channel_id, added_at FROM discord_channels ORDER BY added_at DESC"
    )
    # Convert sqlite3.Row to dataclass instances
    return [DiscordChannel(**dict(row)) for row in rows]


def add_telegram_channel(channel_id: int, username: str, forward: bool = True) -> None:
    """
    Add a Telegram channel to the database.

    Args:
        channel_id: Telegram channel ID
        username: Telegram channel username
        forward: Whether to forward messages from this channel to Discord (default: True)

    Raises:
        ChannelAlreadyExistsError: If channel already exists
        sqlite3.DatabaseError: If database operation fails
    """
    db = services.database
    num_forward = 1 if forward else 0
    try:
        db.execute(
            "INSERT INTO telegram_channels (channel_id, username, forward) VALUES (?, ?, ?)",
            (channel_id, username, num_forward),
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
        "SELECT channel_id, username, added_at, forward FROM telegram_channels ORDER BY added_at DESC"
    )

    # SQLite stores BOOLEAN as INTEGER (0/1), convert to bool
    result: list[TelegramChannel] = []
    for row in rows:
        row_dict = dict(row)
        row_dict["forward"] = bool(row_dict["forward"])
        result.append(TelegramChannel(**row_dict))
    return result
