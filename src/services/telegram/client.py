import logging

import telethon

logger = logging.getLogger(__name__)


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
        user = await client.get_me()
        if user:
            logger.info(f"Logged in as {user.first_name} (@{user.username})")
        else:
            logger.info("Not logged in")
        return client
