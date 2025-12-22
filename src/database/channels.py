from dataclasses import dataclass

from src.database import get_database


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
    db = get_database()

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


def add_discord_channel(channel_id: int) -> tuple[bool, str | None]:
    """
    Args:
        channel_id: Discord channel ID

    Returns:
        Tuple of (success, error_message):
        - (True, None) if added successfully
        - (False, "already_exists") if channel already exists
    """
    db = get_database()
    try:
        db.execute(
            "INSERT INTO discord_channels (channel_id) VALUES (?)",
            (channel_id,),
        )
        return (True, None)
    except Exception:
        return (False, "already_exists")


def remove_discord_channel(channel_id: int) -> tuple[bool, str | None]:
    """
    Args:
        channel_id: Discord channel ID

    Returns:
        Tuple of (success, error_message):
        - (True, None) if removed successfully
        - (False, "not_found") if channel doesn't exist
    """
    db = get_database()
    # Check if channel exists first
    existing = db.fetch_one(
        "SELECT id FROM discord_channels WHERE channel_id = ?",
        (channel_id,),
    )
    if not existing:
        return (False, "not_found")

    db.execute("DELETE FROM discord_channels WHERE channel_id = ?", (channel_id,))
    return (True, None)


def list_discord_channels() -> list[DiscordChannel]:
    """
    Returns:
        List of all stored Discord channels
    """
    db = get_database()
    rows = db.fetch_all(
        "SELECT channel_id, added_at FROM discord_channels ORDER BY added_at DESC"
    )
    # Convert sqlite3.Row to dataclass instances
    return [DiscordChannel(**dict(row)) for row in rows]


def add_telegram_channel(
    channel_id: int, username: str, forward: bool = True
) -> tuple[bool, str | None]:
    """
    Args:
        channel_id: Telegram channel ID
        username: Telegram channel username
        forward: Whether to forward messages from this channel to Discord (default: True)

    Returns:
        Tuple of (success, error_message):
        - (True, None) if added successfully
        - (False, "already_exists") if channel already exists
    """
    db = get_database()
    try:
        num_forward = 1 if forward else 0
        db.execute(
            "INSERT INTO telegram_channels (channel_id, username, forward) VALUES (?, ?, ?)",
            (channel_id, username, num_forward),
        )
        return (True, None)
    except Exception:
        return (False, "already_exists")


def remove_telegram_channel(channel_id: int) -> tuple[bool, str | None]:
    """
    Args:
        channel_id: Telegram channel ID

    Returns:
        Tuple of (success, error_message):
        - (True, None) if removed successfully
        - (False, "not_found") if channel doesn't exist
    """
    db = get_database()
    # Check if channel exists first
    existing = db.fetch_one(
        "SELECT id FROM telegram_channels WHERE channel_id = ?",
        (channel_id,),
    )
    if not existing:
        return (False, "not_found")

    db.execute(
        "DELETE FROM telegram_channels WHERE channel_id = ?",
        (channel_id,),
    )
    return (True, None)


def list_telegram_channels() -> list[TelegramChannel]:
    """
    Returns:
        List of all stored Telegram channels
    """
    db = get_database()
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
