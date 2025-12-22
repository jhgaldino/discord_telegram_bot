import logging

from telethon import TelegramClient

logger = logging.getLogger(__name__)


class TelegramClientManager:
    def __init__(
        self,
        api_id: int,
        api_hash: str,
    ) -> None:
        self.api_id = api_id
        self.api_hash = api_hash
        self.client = TelegramClient("telegram", api_id, api_hash)

    async def connect(self) -> None:
        try:
            await self.client.connect()
            logger.info("Telegram client connected")
        except Exception as e:
            logger.error(f"Failed to connect Telegram client: {e}")

    async def disconnect(self) -> None:
        try:
            await self.client.disconnect()
            logger.info("Telegram client disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting Telegram client: {e}")

    def is_connected(self) -> bool:
        return self.client.is_connected()

    async def is_user_authorized(self) -> bool:
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
            user = await telegram_client.client.get_me()
            if user:
                logger.info(f"Logged in as {user.first_name} (@{user.username})")
            else:
                logger.info("Not logged in")
            return telegram_client
        except Exception as e:
            raise RuntimeError(f"Failed to connect Telegram client: {e}") from e
