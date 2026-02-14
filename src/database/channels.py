from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.database.models import DiscordChannel as DiscordChannelModel
from src.database.models import TelegramChannel as TelegramChannelModel
from src.shared.exceptions import (
    ChannelAlreadyExistsError,
    ChannelNotFoundError,
)
from src.shared.services import services


@dataclass
class DiscordChannel:
    """Data class for Discord channel results."""

    channel_id: int
    added_at: str


@dataclass
class TelegramChannel:
    """Data class for Telegram channel results."""

    channel_id: int
    username: str
    added_at: str
    forward: bool


def add_discord_channel(channel_id: int) -> None:
    """
    Add a Discord channel to the database.

    Args:
        channel_id: Discord channel ID

    Raises:
        ChannelAlreadyExistsError: If channel already exists
    """
    db = services.database
    with db.get_session() as session:
        # Check if channel already exists
        stmt = select(DiscordChannelModel).where(
            DiscordChannelModel.channel_id == channel_id
        )
        existing = session.scalar(stmt)
        if existing:
            raise ChannelAlreadyExistsError(
                f"Discord channel {channel_id} already exists"
            )

        try:
            new_channel = DiscordChannelModel(channel_id=channel_id)
            session.add(new_channel)
            session.flush()
        except IntegrityError:
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
    """
    db = services.database
    with db.get_session() as session:
        stmt = select(DiscordChannelModel).where(
            DiscordChannelModel.channel_id == channel_id
        )
        channel = session.scalar(stmt)
        if not channel:
            raise ChannelNotFoundError(f"Discord channel {channel_id} not found")

        session.delete(channel)


def list_discord_channels() -> list[DiscordChannel]:
    """
    List all Discord channels.

    Returns:
        List of all stored Discord channels
    """
    db = services.database
    with db.get_session() as session:
        stmt = select(DiscordChannelModel).order_by(DiscordChannelModel.added_at.desc())
        channels = session.scalars(stmt).all()

        return [
            DiscordChannel(
                channel_id=channel.channel_id,
                added_at=channel.added_at.isoformat(),
            )
            for channel in channels
        ]


def add_telegram_channel(channel_id: int, username: str, forward: bool = True) -> None:
    """
    Add a Telegram channel to the database.

    Args:
        channel_id: Telegram channel ID
        username: Telegram channel username
        forward: Whether to forward messages from this channel to Discord (default: True)

    Raises:
        ChannelAlreadyExistsError: If channel already exists
    """
    db = services.database
    with db.get_session() as session:
        # Check if channel already exists (by channel_id or username)
        stmt = select(TelegramChannelModel).where(
            (TelegramChannelModel.channel_id == channel_id)
            | (TelegramChannelModel.username == username)
        )
        existing = session.scalar(stmt)
        if existing:
            raise ChannelAlreadyExistsError(
                f"Telegram channel {channel_id} ({username}) already exists"
            )

        try:
            new_channel = TelegramChannelModel(
                channel_id=channel_id, username=username, forward=forward
            )
            session.add(new_channel)
            session.flush()
        except IntegrityError:
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
    """
    db = services.database
    with db.get_session() as session:
        stmt = select(TelegramChannelModel).where(
            TelegramChannelModel.channel_id == channel_id
        )
        channel = session.scalar(stmt)
        if not channel:
            raise ChannelNotFoundError(f"Telegram channel {channel_id} not found")

        session.delete(channel)


def list_telegram_channels() -> list[TelegramChannel]:
    """
    List all Telegram channels.

    Returns:
        List of all stored Telegram channels
    """
    db = services.database
    with db.get_session() as session:
        stmt = select(TelegramChannelModel).order_by(
            TelegramChannelModel.added_at.desc()
        )
        channels = session.scalars(stmt).all()

        return [
            TelegramChannel(
                channel_id=channel.channel_id,
                username=channel.username,
                added_at=channel.added_at.isoformat(),
                forward=channel.forward,
            )
            for channel in channels
        ]
