"""Message forwarder service for forwarding messages from Telegram to Discord."""

import asyncio
import logging
import re

from discord.channel import PartialMessageable
from telethon import events

from src.config import get_bot, get_client
from src.shared import reminders
from src.shared.utils import format_list_to_markdown

logger = logging.getLogger(__name__)


class MessageForwarder:
    """Service that forwards messages from Telegram to Discord channels."""

    def __init__(
        self,
        telegram_channels: list[str],
        discord_channel_ids: list[int],
    ) -> None:
        """
        Initialize the message forwarder.

        Args:
            telegram_channels: List of Telegram channel usernames/IDs to monitor
            discord_channel_ids: List of Discord channel IDs to forward messages to
        """
        self.telegram_channels = telegram_channels
        self.discord_channel_ids = discord_channel_ids
        self._discord_channels: set[PartialMessageable] = set()
        self._event_handlers_registered = False

    def _filter(self, event: events.NewMessage.Event) -> bool:
        """Filter function to check if message contains URLs."""
        if re.search(r"https://", event.raw_text):
            return True
        return False

    def _format(self, event: events.NewMessage.Event) -> str:
        """Format Telegram message text."""
        text = re.sub(r"\n+", "\n", event.raw_text)
        return text

    async def _send_dm_to_user(self, message: str, user_id: int) -> None:
        """Send a direct message to a Discord user."""
        bot = get_bot()
        user = await bot.fetch_user(user_id)
        await user.send(message)

    def start(self) -> None:
        """Start forwarding messages."""
        if self._event_handlers_registered:
            return

        telegram_client = get_client()

        for telegram_channel in self.telegram_channels:
            # Capture telegram_channel in closure to avoid late binding issue
            channel = telegram_channel

            @telegram_client.client.on(
                events.NewMessage(chats=channel, func=self._filter)
            )
            async def my_event_handler(event: events.NewMessage.Event) -> None:
                text_to_channel = self._format(event)

                tasks = []

                for discord_channel in self._discord_channels:
                    if discord_channel:
                        tasks.append(discord_channel.send(text_to_channel))

                reminder_by_user = reminders.find_by_user_in_text(text_to_channel)
                for user_id, reminder_list in reminder_by_user.items():
                    markdown_list = format_list_to_markdown(reminder_list)
                    text_to_user = (
                        text_to_channel
                        + f"\n\nVocê me pediu para te lembrar de:\n{markdown_list}"
                    )
                    tasks.append(self._send_dm_to_user(text_to_user, user_id))

                await asyncio.gather(*tasks)

        self._event_handlers_registered = True

    def stop(self) -> None:
        """Stop forwarding messages."""
        # Note: Telethon doesn't provide a direct way to unregister handlers
        self._event_handlers_registered = False

    def update_discord_channels(self) -> None:
        """Update the set of Discord channels from channel IDs."""
        bot = get_bot()
        self._discord_channels.clear()
        for channel_id in self.discord_channel_ids:
            channel = bot.get_partial_messageable(channel_id)
            if channel:
                self._discord_channels.add(channel)

    async def on_bot_ready(self) -> None:
        """Called when the Discord bot is ready."""
        self.update_discord_channels()
        for channel in self._discord_channels:
            try:
                await channel.send("Bot is ready.")
            except Exception as e:
                logger.error(f"Failed to send ready message to {channel}: {e}")
