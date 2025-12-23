import asyncio
import logging
import re
import sqlite3
from types import CoroutineType

import discord.errors
from discord.channel import PartialMessageable
from telethon import utils
from telethon.events import NewMessage
from telethon.tl.types import Message

from src.database import channels as channel_db
from src.database import reminders
from src.database.channels import TelegramChannel
from src.shared.exceptions import ChannelNotFoundError
from src.shared.services import services
from src.shared.utils import format_list_to_markdown

logger = logging.getLogger(__name__)


class MessageForwarder:
    """Service that forwards messages from Telegram to Discord channels."""

    def __init__(self) -> None:
        self._discord_channels: set[PartialMessageable] = set()
        self._telegram_channels: dict[int, TelegramChannel] = {}
        self._event_handlers_registered = False

    def _load_telegram_channels(self) -> None:
        channels = channel_db.list_telegram_channels()
        self._telegram_channels.clear()
        for channel in channels:
            self._telegram_channels[channel.channel_id] = channel

    def _load_discord_channels(self) -> None:
        self._discord_channels.clear()
        channels = channel_db.list_discord_channels()
        for channel in channels:
            channel = services.bot.get_partial_messageable(channel.channel_id)
            if channel:
                self._discord_channels.add(channel)

    def _filter_message_event(self, event: NewMessage.Event) -> bool:
        message: Message = event.message
        if re.search(r"https://", message.message):
            return True
        return False

    def _format_message(self, message: Message) -> str:
        text = re.sub(r"\n+", "\n", message.message)
        return text

    async def _send_dm_to_user(self, message: str, user_id: int) -> None:
        """Send a direct message to a Discord user."""
        user = await services.bot.fetch_user(user_id)
        await user.send(message)

    async def _forward_message_handler(self, event: NewMessage.Event) -> None:
        """Handler function for forwarding messages from Telegram to Discord."""
        message: Message = event.message
        text_to_channel = self._format_message(message)

        # event.chat_id returns a marked ID (e.g., -100123456789), convert to real channel ID
        channel_id, _ = utils.resolve_id(event.chat_id)
        tasks: list[CoroutineType] = []

        # Check if this channel should forward to Discord
        telegram_channel = self._telegram_channels.get(channel_id)
        if telegram_channel and telegram_channel.forward:
            # Only forward to Discord channels if channel is in our list and forward is enabled
            for discord_channel in self._discord_channels:
                if discord_channel:
                    tasks.append(discord_channel.send(text_to_channel))

        # Always send reminders regardless of forward setting or channel presence
        reminder_by_user = reminders.find_matching_reminders(message.message)
        for user_id, group_names in reminder_by_user.items():
            markdown_list = format_list_to_markdown(group_names)
            text_to_user = (
                text_to_channel
                + f"\n\nVocê me pediu para te lembrar dos grupos:\n{markdown_list}"
            )
            tasks.append(self._send_dm_to_user(text_to_user, user_id))

        await asyncio.gather(*tasks)

    def _register_handlers(self) -> None:
        """Register event handlers for all Telegram channels."""
        # Get set of channel IDs for event handler
        channel_ids = set(self._telegram_channels.keys())
        event_builder = NewMessage(chats=channel_ids, func=self._filter_message_event)
        services.client.add_event_handler(self._forward_message_handler, event_builder)

    def _unregister_handlers(self) -> None:
        """Unregister all event handlers for the forwarder."""
        # Find all handlers registered for our handler function
        # Since we use the same handler for all channels, we can remove all at once
        registered_handlers = services.client.list_event_handlers()

        # Remove all handlers that use our forward_message_handler
        for callback, event_builder in registered_handlers:
            if callback == self._forward_message_handler:
                services.client.remove_event_handler(callback, event_builder)

    def start(self) -> None:
        """Start forwarding messages."""
        if self._event_handlers_registered:
            return

        self._register_handlers()
        self._event_handlers_registered = True

    def stop(self) -> None:
        """Stop forwarding messages."""
        self._unregister_handlers()
        self._event_handlers_registered = False

    def reload_channels(self) -> None:
        """Reload channels from database and update event handlers."""
        old_channel_ids = set(self._telegram_channels.keys())

        self._load_discord_channels()
        self._load_telegram_channels()

        # If handlers are registered and Telegram channels changed, reload handlers
        new_channel_ids = set(self._telegram_channels.keys())
        if self._event_handlers_registered and old_channel_ids != new_channel_ids:
            logger.info("Telegram channels changed, reloading event handlers")
            self._unregister_handlers()
            self._register_handlers()

    async def on_bot_ready(self) -> None:
        self._load_discord_channels()
        self._load_telegram_channels()

        for channel in self._discord_channels:
            try:
                await channel.send("Bot online")
            except discord.errors.Forbidden:
                logger.warning(
                    f"Lost access to channel '{channel.id}'. Removing from database."
                )
                try:
                    channel_db.remove_discord_channel(channel.id)
                except (sqlite3.DatabaseError, ChannelNotFoundError) as e:
                    logger.error(
                        f"Failed to remove channel '{channel.id}' from database: {e}",
                        exc_info=e,
                    )
            except (discord.errors.HTTPException, discord.errors.NotFound) as e:
                logger.warning(
                    f"Failed to send ready message to channel '{channel.id}': {e}"
                )

        self._load_discord_channels()
