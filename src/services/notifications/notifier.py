import asyncio
import logging
import re

import discord
from telethon.events import NewMessage
from telethon.tl.types import Message

from src.database import channels as channel_db
from src.database import reminders
from src.database.reminders import ReminderGroupsByUser
from src.shared.services import services
from src.shared.utils import format_list_to_markdown

logger = logging.getLogger(__name__)


class ReminderNotifier:
    """Send opt-in Discord DMs for matching Telegram channel messages."""

    def __init__(self) -> None:
        self._telegram_channels: set[int] = set()
        self._reminder_groups: ReminderGroupsByUser = {}
        self._event_builder: NewMessage | None = None
        self._registered_channels: frozenset[int] = frozenset()
        self._running = False

    @staticmethod
    def _filter_message_event(event: NewMessage.Event) -> bool:
        message: Message = event.message
        return re.search(r"https://", message.message) is not None

    @staticmethod
    def _format_message(message: Message) -> str:
        return re.sub(r"\n+", "\n", message.message)

    async def _send_dm_to_user(self, message: str, user_id: int) -> None:
        try:
            user = services.bot.get_user(user_id)
            if user is None:
                user = await services.bot.fetch_user(user_id)
            await user.send(message, suppress_embeds=True)
        except (discord.Forbidden, discord.NotFound, discord.HTTPException) as error:
            logger.warning("Could not send reminder DM to user %s: %s", user_id, error)

    async def _handle_message(self, event: NewMessage.Event) -> None:
        message: Message = event.message
        matches = reminders.find_matching_reminders(
            message.message, self._reminder_groups
        )
        if not matches:
            return

        formatted_message = self._format_message(message)
        await asyncio.gather(
            *(
                self._send_dm_to_user(
                    formatted_message
                    + "\n\nVocê me pediu para te lembrar dos grupos:\n"
                    + format_list_to_markdown(group_names),
                    user_id,
                )
                for user_id, group_names in matches.items()
            )
        )

    def _register_handler(self, channel_ids: frozenset[int]) -> None:
        self._event_builder = NewMessage(
            chats=set(channel_ids), func=self._filter_message_event
        )
        services.client.add_event_handler(self._handle_message, self._event_builder)
        self._registered_channels = channel_ids

    def _unregister_handler(self) -> None:
        if self._event_builder is None:
            return

        services.client.remove_event_handler(self._handle_message, self._event_builder)
        self._event_builder = None
        self._registered_channels = frozenset()

    def _reconcile_handler(self) -> None:
        desired_channels = frozenset(self._telegram_channels)
        should_register = (
            self._running and bool(desired_channels) and bool(self._reminder_groups)
        )

        if not should_register:
            self._unregister_handler()
            return

        if self._event_builder is not None and (
            self._registered_channels == desired_channels
        ):
            return

        self._unregister_handler()
        self._register_handler(desired_channels)

    def start(self) -> None:
        self._running = True
        self.reload_channels()
        self.reload_reminders()

    def stop(self) -> None:
        self._running = False
        self._unregister_handler()

    def reload_channels(self) -> None:
        self._telegram_channels = {
            channel.channel_id for channel in channel_db.list_telegram_channels()
        }
        self._reconcile_handler()

    def reload_reminders(self) -> None:
        self._reminder_groups = reminders.list_all_groups_by_user()
        self._reconcile_handler()
