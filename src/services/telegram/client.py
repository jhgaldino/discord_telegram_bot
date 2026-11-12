import logging
from datetime import UTC, datetime
from inspect import isawaitable

import telethon
from telethon.tl.functions.account import UpdateNotifySettingsRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import (
    Channel,
    InputChannel,
    InputNotifyPeer,
    InputPeerChannel,
    InputPeerNotifySettings,
    User,
)

from src.shared.utils import format_telegram_account

logger = logging.getLogger(__name__)

_ARCHIVE_FOLDER_ID = 1
_MAX_MUTE_UNTIL = datetime.fromtimestamp(2**31 - 1, tz=UTC)


class TelegramClient(telethon.TelegramClient):
    def __init__(
        self,
        api_id: int,
        api_hash: str,
    ) -> None:
        super().__init__("telegram", api_id, api_hash)
        self.api_id = api_id
        self.api_hash = api_hash

    async def connect(self) -> None:
        await super().connect()
        logger.info("Telegram client connected")

    async def disconnect(self) -> None:
        await super().disconnect()
        logger.info("Telegram client disconnected")

    async def log_out_and_recreate(self) -> TelegramClient:
        """Log out, discard the local session, and return a fresh client.

        Telethon clients cannot be reused after ``log_out`` because that method
        deletes their session and sets it to ``None``. A stale/invalid session
        may also make the remote logout fail, so the local session is deleted as
        a fallback before creating the replacement.
        """
        session = self.session
        logged_out = False

        if self.is_connected():
            logged_out = await super().log_out()

        if not logged_out:
            if self.is_connected():
                await self.disconnect()

            if session is not None:
                deletion_result = session.delete()
                if isawaitable(deletion_result):
                    await deletion_result

        return type(self)(api_id=self.api_id, api_hash=self.api_hash)

    async def ensure_channel_subscription(self, channel: Channel) -> bool:
        """Subscribe, archive, and mute a channel unless already subscribed."""
        if channel.left is not True:
            return False

        if channel.access_hash is None:
            raise ValueError("Telegram channel access hash is required")

        input_channel = InputChannel(channel.id, channel.access_hash)
        input_peer = InputPeerChannel(channel.id, channel.access_hash)
        await self(JoinChannelRequest(input_channel))

        try:
            await self.edit_folder(input_peer, _ARCHIVE_FOLDER_ID)
        except Exception:
            logger.warning(
                "Failed to archive newly subscribed Telegram channel %s",
                channel.id,
                exc_info=True,
            )

        try:
            await self(
                UpdateNotifySettingsRequest(
                    peer=InputNotifyPeer(input_peer),
                    settings=InputPeerNotifySettings(mute_until=_MAX_MUTE_UNTIL),
                )
            )
        except Exception:
            logger.warning(
                "Failed to mute newly subscribed Telegram channel %s",
                channel.id,
                exc_info=True,
            )

        return True

    @classmethod
    async def create_and_connect(
        cls,
        api_id: int,
        api_hash: str,
    ) -> TelegramClient:
        """
        Create and connect a Telegram client.

        Raises ValueError if credentials are missing.
        Raises RuntimeError if connection fails.
        """
        if not api_id or not api_hash:
            raise ValueError("Telegram API credentials are required")

        client = cls(api_id=api_id, api_hash=api_hash)
        await client.connect()
        me = await client.get_me()
        if isinstance(me, User):
            account = format_telegram_account(me)
            logger.info(f"Logged in as {account}")
        else:
            logger.info("Not logged in")
        return client
