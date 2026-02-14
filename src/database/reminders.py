from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database.models import ReminderGroup as ReminderGroupModel
from src.database.models import ReminderText
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
    """Data class for reminder group results."""

    group_name: str
    texts: list[str]


# Constants
DEFAULT_GROUP_NAME = "Padrão"
MAX_GROUPS_PER_USER = 25
MAX_TEXTS_PER_GROUP = 25


def _get_group(
    session: Session, user_id: int, group_name: str
) -> ReminderGroupModel | None:
    """
    Get reminder group by user_id and group_name.

    Args:
        session: SQLAlchemy session
        user_id: Discord user ID
        group_name: Name of the group

    Returns:
        ReminderGroupModel if found, None otherwise
    """
    stmt = select(ReminderGroupModel).where(
        ReminderGroupModel.user_id == user_id,
        ReminderGroupModel.group_name == group_name,
    )
    return session.scalar(stmt)


def create_group(user_id: int, group_name: str) -> None:
    """
    Create a new reminder group for a user.

    Args:
        user_id: Discord user ID
        group_name: Name of the group

    Raises:
        ReminderGroupAlreadyExistsError: If group already exists
        ReminderLimitReachedError: If user has reached max groups
    """
    db = services.database
    with db.get_session() as session:
        # Check if group already exists
        existing = _get_group(session, user_id, group_name)
        if existing is not None:
            raise ReminderGroupAlreadyExistsError(
                f"Reminder group '{group_name}' already exists for user {user_id}"
            )

        # Check if user has reached max groups
        stmt = select(func.count(ReminderGroupModel.id)).where(
            ReminderGroupModel.user_id == user_id
        )
        user_groups_count = session.scalar(stmt) or 0
        if user_groups_count >= MAX_GROUPS_PER_USER:
            raise ReminderLimitReachedError(
                f"User {user_id} has reached the maximum of {MAX_GROUPS_PER_USER} reminder groups"
            )

        # Create new group
        try:
            new_group = ReminderGroupModel(
                user_id=user_id,
                group_name=group_name,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            session.add(new_group)
            session.flush()
        except IntegrityError:
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
    """
    db = services.database
    with db.get_session() as session:
        group = _get_group(session, user_id, group_name)
        if not group:
            raise ReminderGroupNotFoundError(
                f"Reminder group '{group_name}' not found for user {user_id}"
            )

        # Check if group has reached max texts
        stmt = select(func.count(ReminderText.id)).where(
            ReminderText.group_id == group.id
        )
        texts_count = session.scalar(stmt) or 0
        if texts_count >= MAX_TEXTS_PER_GROUP:
            raise ReminderLimitReachedError(
                f"Reminder group '{group_name}' has reached the maximum of {MAX_TEXTS_PER_GROUP} texts"
            )

        # Sanitize text before saving
        sanitized = sanitize_text(text)

        # Add text to group
        try:
            new_text = ReminderText(group_id=group.id, text=sanitized)
            session.add(new_text)
            # Update group's updated_at timestamp
            group.updated_at = datetime.now(UTC)
            session.flush()
        except IntegrityError:
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
    """
    db = services.database
    with db.get_session() as session:
        group = _get_group(session, user_id, group_name)
        if not group:
            raise ReminderGroupNotFoundError(
                f"Reminder group '{group_name}' not found for user {user_id}"
            )

        # Sanitize text for matching
        sanitized = sanitize_text(text)

        # Remove text from group
        stmt = select(ReminderText).where(
            ReminderText.group_id == group.id, ReminderText.text == sanitized
        )
        text_obj = session.scalar(stmt)
        if text_obj:
            session.delete(text_obj)
            # Update group's updated_at timestamp
            group.updated_at = datetime.now(UTC)

        # Check if group is now empty
        stmt = select(func.count(ReminderText.id)).where(
            ReminderText.group_id == group.id
        )
        remaining_texts_count = session.scalar(stmt) or 0

        if remaining_texts_count == 0:
            # Group is empty, delete it
            session.delete(group)
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
        List of ReminderGroup dataclass instances with group_name and texts
    """
    db = services.database
    with db.get_session() as session:
        stmt = (
            select(ReminderGroupModel)
            .where(ReminderGroupModel.user_id == user_id)
            .order_by(ReminderGroupModel.updated_at.desc())
        )

        if group_name is not None:
            stmt = stmt.where(ReminderGroupModel.group_name == group_name)

        groups = session.scalars(stmt).all()

        result: list[ReminderGroup] = []
        for group_model in groups:
            # Access texts through relationship (already loaded with selectin)
            texts = [text.text for text in group_model.texts]
            result.append(ReminderGroup(group_name=group_model.group_name, texts=texts))

        return result


def delete_group(user_id: int, group_name: str) -> None:
    """
    Delete a reminder group and all its texts.

    Args:
        user_id: Discord user ID
        group_name: Name of the group to delete

    Raises:
        ReminderGroupNotFoundError: If group doesn't exist
    """
    db = services.database
    with db.get_session() as session:
        group = _get_group(session, user_id, group_name)
        if not group:
            raise ReminderGroupNotFoundError(
                f"Reminder group '{group_name}' not found for user {user_id}"
            )

        session.delete(group)
        # Cascade delete will handle texts automatically


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

    with db.get_session() as session:
        # Get all groups with their texts
        stmt = select(ReminderGroupModel).order_by(
            ReminderGroupModel.user_id, ReminderGroupModel.id
        )
        groups = session.scalars(stmt).all()

        # Group by user_id and group_name, collecting texts
        groups_by_user: dict[int, dict[str, list[str]]] = {}
        for group in groups:
            user_id = group.user_id
            group_name = group.group_name

            if user_id not in groups_by_user:
                groups_by_user[user_id] = {}
            if group_name not in groups_by_user[user_id]:
                groups_by_user[user_id][group_name] = []

            # Access texts through relationship
            for text_obj in group.texts:
                if text_obj.text:
                    groups_by_user[user_id][group_name].append(text_obj.text)

        # Check which groups have all texts matching
        reminder_by_user: dict[int, list[str]] = {}
        for user_id, groups_dict in groups_by_user.items():
            for group_name, texts in groups_dict.items():
                if texts and all(text_val in text_sanitized for text_val in texts):
                    if user_id not in reminder_by_user:
                        reminder_by_user[user_id] = []
                    reminder_by_user[user_id].append(group_name)

        return reminder_by_user
