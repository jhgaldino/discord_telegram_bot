"""Telegram client manager for handling Telegram connection."""

import logging

from telethon import TelegramClient

logger = logging.getLogger(__name__)


class TelegramClientManager:
    """Manages Telegram client connection."""

    def __init__(
        self,
        api_id: int,
        api_hash: str,
    ) -> None:
        """
        Initialize the Telegram client manager.

        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.client = TelegramClient("telegram", api_id, api_hash)

    async def connect(self) -> None:
        """Connect to Telegram."""
        await self.client.connect()
        user = await self.client.get_me()
        logger.info(
            f"Telegram client connected as {user.first_name} (@{user.username})"
        )

    async def disconnect(self) -> None:
        """Disconnect from Telegram."""
        try:
            await self.client.disconnect()
            logger.info("Telegram client disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting Telegram client: {e}")

    def is_connected(self) -> bool:
        """Check if Telegram client is connected."""
        return self.client.is_connected()

    async def is_user_authorized(self) -> bool:
        """Check if Telegram user is authorized."""
        return await self.client.is_user_authorized()

    @classmethod
    async def create_and_connect(
        cls,
        api_id: int,
        api_hash: str,
    ) -> "TelegramClientManager":
        """
        Create and connect a Telegram client.

        Raises ValueError if credentials are missing.
        Raises RuntimeError if connection fails.
        """
        if not api_id or not api_hash:
            raise ValueError("Telegram API credentials are required")

        telegram_client = cls(
            api_id=api_id,
            api_hash=api_hash,
        )
        try:
            await telegram_client.connect()
            logger.info("Telegram client connected")
            return telegram_client
        except Exception as e:
            logger.error(f"Failed to connect Telegram client: {e}")
            raise RuntimeError(f"Failed to connect Telegram client: {e}") from e
