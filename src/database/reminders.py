import sqlite3
from dataclasses import dataclass

from src.shared.exceptions import (
    ReminderGroupAlreadyExistsError,
    ReminderGroupNotFoundError,
    ReminderLimitReachedError,
    ReminderTextExistsError,
)
from src.shared.services import services
from src.shared.utils import sanitize_text


@dataclass
class ReminderGroup:
    group_name: str
    texts: list[str]


# Constants
DEFAULT_GROUP_NAME = "Padrão"
MAX_GROUPS_PER_USER = 25
MAX_TEXTS_PER_GROUP = 25


def _init_reminders_tables() -> None:
    db = services.database

    # Create reminder_groups table
    if not db.table_exists("reminder_groups"):
        create_groups_table = """
            CREATE TABLE reminder_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                group_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, group_name)
            )
        """
        db.create_table_if_not_exists(create_groups_table)

    # Create reminder_texts table
    if not db.table_exists("reminder_texts"):
        create_texts_table = """
            CREATE TABLE reminder_texts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                FOREIGN KEY (group_id) REFERENCES reminder_groups(id) ON DELETE CASCADE,
                UNIQUE(group_id, text)
            )
        """
        db.create_table_if_not_exists(create_texts_table)

    # Create triggers to auto-update updated_at when texts are added/removed
    _create_update_triggers()

    # Migrate old reminders table if it exists
    if db.table_exists("reminders") and not db.table_exists("_reminders_migrated"):
        _migrate_old_reminders()
        # Mark migration as complete
        db.execute(
            """
            CREATE TABLE _reminders_migrated (
                id INTEGER PRIMARY KEY
            )
        """
        )


def _create_update_triggers() -> None:
    db = services.database
    # Drop existing triggers if they exist (to allow re-running)
    # DROP TRIGGER IF EXISTS won't raise an exception, so no try/except needed
    db.execute("DROP TRIGGER IF EXISTS update_group_on_text_insert")
    db.execute("DROP TRIGGER IF EXISTS update_group_on_text_delete")

    # Trigger to update updated_at when a text is added
    db.execute("""
        CREATE TRIGGER update_group_on_text_insert
        AFTER INSERT ON reminder_texts
        BEGIN
            UPDATE reminder_groups
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.group_id;
        END
    """)

    # Trigger to update updated_at when a text is removed
    db.execute("""
        CREATE TRIGGER update_group_on_text_delete
        AFTER DELETE ON reminder_texts
        BEGIN
            UPDATE reminder_groups
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = OLD.group_id;
        END
    """)


def _migrate_old_reminders() -> None:
    db = services.database
    try:
        # Get all old reminders
        old_reminders = db.fetch_all(
            "SELECT user_id, reminder FROM reminders GROUP BY user_id, reminder"
        )

        for row in old_reminders:
            user_id = row["user_id"]
            reminder_text = row["reminder"]

            # Get or create default group for each user
            group_result = db.fetch_one(
                "SELECT id FROM reminder_groups WHERE user_id = ? AND group_name = ?",
                (user_id, DEFAULT_GROUP_NAME),
            )

            if not group_result:
                # Create default group
                db.execute(
                    "INSERT INTO reminder_groups (user_id, group_name) VALUES (?, ?)",
                    (user_id, DEFAULT_GROUP_NAME),
                )
                group_result = db.fetch_one(
                    "SELECT id FROM reminder_groups WHERE user_id = ? AND group_name = ?",
                    (user_id, DEFAULT_GROUP_NAME),
                )

            if group_result:
                group_id = group_result["id"]
                # Add reminder text to group
                try:
                    sanitized_text = sanitize_text(reminder_text)
                    db.execute(
                        "INSERT INTO reminder_texts (group_id, text) VALUES (?, ?)",
                        (group_id, sanitized_text),
                    )
                except sqlite3.IntegrityError:
                    # Already exists, skip
                    pass
    except Exception:
        # Migration failed, but don't break the app
        pass


# Initialize tables on module import
_init_reminders_tables()


def _get_group_id(user_id: int, group_name: str) -> int | None:
    """
    Get group ID by user_id and group_name.

    Args:
        user_id: Discord user ID
        group_name: Name of the group

    Returns:
        Group ID if found, None otherwise
    """
    db = services.database
    result = db.fetch_one(
        "SELECT id FROM reminder_groups WHERE user_id = ? AND group_name = ?",
        (user_id, group_name),
    )
    return result["id"] if result else None


def create_group(user_id: int, group_name: str) -> None:
    """
    Create a new reminder group for a user.

    Args:
        user_id: Discord user ID
        group_name: Name of the group

    Raises:
        ReminderGroupAlreadyExistsError: If group already exists
        ReminderLimitReachedError: If user has reached max groups
        sqlite3.DatabaseError: If database operation fails
    """
    db = services.database

    # Check if group already exists first
    if _get_group_id(user_id, group_name) is not None:
        raise ReminderGroupAlreadyExistsError(
            f"Reminder group '{group_name}' already exists for user {user_id}"
        )

    # Check if user has reached max groups (only for new groups)
    user_groups_count = db.fetch_one(
        "SELECT COUNT(*) as count FROM reminder_groups WHERE user_id = ?",
        (user_id,),
    )
    if user_groups_count and user_groups_count["count"] >= MAX_GROUPS_PER_USER:
        raise ReminderLimitReachedError(
            f"User {user_id} has reached the maximum of {MAX_GROUPS_PER_USER} reminder groups"
        )

    try:
        db.execute(
            "INSERT INTO reminder_groups (user_id, group_name) VALUES (?, ?)",
            (user_id, group_name),
        )
    except sqlite3.IntegrityError:
        # Should not happen since we checked existence, but handle just in case
        raise ReminderGroupAlreadyExistsError(
            f"Reminder group '{group_name}' already exists for user {user_id}"
        ) from None


def add_text_to_group(user_id: int, group_name: str, text: str) -> None:
    """
    Add a text to a reminder group.

    Args:
        user_id: Discord user ID
        group_name: Name of the group
        text: Text to add to the group

    Raises:
        ReminderGroupNotFoundError: If group doesn't exist
        ReminderTextExistsError: If text already exists in group
        ReminderLimitReachedError: If group has reached max texts
        sqlite3.DatabaseError: If database operation fails
    """
    group_id = _get_group_id(user_id, group_name)
    if not group_id:
        raise ReminderGroupNotFoundError(
            f"Reminder group '{group_name}' not found for user {user_id}"
        )

    db = services.database

    # Check if group has reached max texts
    texts_count = db.fetch_one(
        "SELECT COUNT(*) as count FROM reminder_texts WHERE group_id = ?",
        (group_id,),
    )
    if texts_count and texts_count["count"] >= MAX_TEXTS_PER_GROUP:
        raise ReminderLimitReachedError(
            f"Reminder group '{group_name}' has reached the maximum of {MAX_TEXTS_PER_GROUP} texts"
        )

    # Sanitize text before saving
    sanitized = sanitize_text(text)
    try:
        db.execute(
            "INSERT INTO reminder_texts (group_id, text) VALUES (?, ?)",
            (group_id, sanitized),
        )
    except sqlite3.IntegrityError:
        raise ReminderTextExistsError(
            f"Text already exists in reminder group '{group_name}'"
        ) from None


def remove_text_from_group(user_id: int, group_name: str, text: str) -> bool:
    """
    Remove a text from a reminder group. Automatically deletes the group if it becomes empty.

    Args:
        user_id: Discord user ID
        group_name: Name of the group
        text: Text to remove from the group

    Returns:
        True if group was deleted (was empty), False if group still has texts

    Raises:
        ReminderGroupNotFoundError: If group doesn't exist
        sqlite3.DatabaseError: If database operation fails
    """
    group_id = _get_group_id(user_id, group_name)
    if not group_id:
        raise ReminderGroupNotFoundError(
            f"Reminder group '{group_name}' not found for user {user_id}"
        )

    db = services.database

    # Sanitize text for matching
    sanitized = sanitize_text(text)
    db.execute(
        "DELETE FROM reminder_texts WHERE group_id = ? AND text = ?",
        (group_id, sanitized),
    )

    # Check if group is now empty
    remaining_texts = db.fetch_one(
        "SELECT COUNT(*) as count FROM reminder_texts WHERE group_id = ?",
        (group_id,),
    )

    if remaining_texts and remaining_texts["count"] == 0:
        # Group is empty, delete it
        db.execute("DELETE FROM reminder_groups WHERE id = ?", (group_id,))
        return True
    return False


def list_groups_by_user(
    user_id: int, group_name: str | None = None
) -> list[ReminderGroup]:
    """
    List groups for a user with their texts.

    Args:
        user_id: Discord user ID
        group_name: Optional group name to filter by. If None, returns all groups.

    Returns:
        List of dictionaries with group_name (str) and texts (list[str])
    """
    db = services.database
    if group_name is not None:
        rows = db.fetch_all(
            """
            SELECT rg.group_name, rt.text
            FROM reminder_groups rg
            LEFT JOIN reminder_texts rt ON rg.id = rt.group_id
            WHERE rg.user_id = ? AND rg.group_name = ?
            ORDER BY rg.updated_at DESC, rt.text
        """,
            (user_id, group_name),
        )
    else:
        rows = db.fetch_all(
            """
            SELECT rg.group_name, rt.text
            FROM reminder_groups rg
            LEFT JOIN reminder_texts rt ON rg.id = rt.group_id
            WHERE rg.user_id = ?
            ORDER BY rg.updated_at DESC, rt.text
        """,
            (user_id,),
        )

    groups: dict[str, list[str]] = {}
    for row in rows:
        group_name = row["group_name"]
        text = row["text"]
        if group_name not in groups:
            groups[group_name] = []
        if text:
            groups[group_name].append(text)

    result: list[ReminderGroup] = []
    for name, texts in groups.items():
        result.append(ReminderGroup(group_name=name, texts=texts))
    return result


def delete_group(user_id: int, group_name: str) -> None:
    """
    Delete a reminder group and all its texts.

    Args:
        user_id: Discord user ID
        group_name: Name of the group to delete

    Raises:
        ReminderGroupNotFoundError: If group doesn't exist
        sqlite3.DatabaseError: If database operation fails
    """
    group_id = _get_group_id(user_id, group_name)
    if not group_id:
        raise ReminderGroupNotFoundError(
            f"Reminder group '{group_name}' not found for user {user_id}"
        )

    db = services.database
    db.execute("DELETE FROM reminder_groups WHERE id = ?", (group_id,))


def find_matching_reminders(text: str) -> dict[int, list[str]]:
    """
    Find users whose reminder groups match the given text (all texts in group must match).

    Args:
        text: Text to search for reminders in (will be sanitized internally)

    Returns:
        Dictionary mapping user IDs to lists of matching group names
    """
    db = services.database
    # Sanitize input text for matching (stored texts are already sanitized)
    text_sanitized = sanitize_text(text)

    # Single query with JOIN to get all groups with their texts
    groups_with_texts = db.fetch_all(
        """
        SELECT rg.user_id, rg.group_name, rt.text
        FROM reminder_groups rg
        LEFT JOIN reminder_texts rt ON rg.id = rt.group_id
        ORDER BY rg.user_id, rg.id
    """
    )

    # Group by user_id and group_name, collecting texts
    groups_by_user: dict[int, dict[str, list[str]]] = {}
    for row in groups_with_texts:
        user_id = row["user_id"]
        group_name = row["group_name"]
        text_val = row["text"]

        if user_id not in groups_by_user:
            groups_by_user[user_id] = {}
        if group_name not in groups_by_user[user_id]:
            groups_by_user[user_id][group_name] = []
        if text_val:
            groups_by_user[user_id][group_name].append(text_val)

    # Check which groups have all texts matching
    reminder_by_user: dict[int, list[str]] = {}
    for user_id, groups in groups_by_user.items():
        for group_name, texts in groups.items():
            if texts and all(text_val in text_sanitized for text_val in texts):
                if user_id not in reminder_by_user:
                    reminder_by_user[user_id] = []
                reminder_by_user[user_id].append(group_name)

    return reminder_by_user
