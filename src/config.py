import asyncio
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from dotenv import load_dotenv

from src.services.discord.bot import Bot
from src.services.telegram.client import TelegramClientManager

if TYPE_CHECKING:
    from src.services.integration.forwarder import MessageForwarder

load_dotenv()


@dataclass
class Config:
    """Application configuration from environment variables."""

    discord_token: str
    telegram_api_id: int
    telegram_api_hash: str

    @staticmethod
    def _get_required_env(var_name: str) -> str:
        """Get a required environment variable or raise ValueError."""
        value = os.getenv(var_name)
        if not value:
            raise ValueError(
                f"{var_name} environment variable is not set. Please set it in your .env file."
            )
        return value

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        discord_token = cls._get_required_env("DISCORD_TOKEN")

        telegram_api_id_str = cls._get_required_env("TELEGRAM_API_ID")
        telegram_api_id = int(telegram_api_id_str)

        telegram_api_hash = cls._get_required_env("TELEGRAM_API_HASH")

        return cls(
            discord_token=discord_token,
            telegram_api_id=telegram_api_id,
            telegram_api_hash=telegram_api_hash,
        )


config = Config.from_env()

_bot: Bot | None = None
_client: TelegramClientManager | None = None
_forwarder: MessageForwarder | None = None


def get_bot() -> Bot:
    """Get the Discord bot instance. Raises RuntimeError if not initialized."""
    if _bot is None:
        raise RuntimeError("Bot has not been initialized yet. Call initialize() first.")
    return _bot


def get_client() -> TelegramClientManager:
    """
    Get the Telegram client instance.

    Raises RuntimeError if initialize() has not been called yet.
    """
    if _client is None:
        raise RuntimeError(
            "Telegram client has not been initialized yet. Call initialize() first."
        )
    return _client


def get_forwarder() -> MessageForwarder:
    """
    Get the message forwarder instance.

    Raises RuntimeError if forwarder has not been initialized yet.
    """
    if _forwarder is None:
        raise RuntimeError(
            "Message forwarder has not been initialized yet. Call set_forwarder() first."
        )
    return _forwarder


def set_forwarder(forwarder: MessageForwarder) -> None:
    """Set the global message forwarder instance."""
    global _forwarder
    _forwarder = forwarder


async def initialize() -> None:
    """
    Initialize Discord bot and Telegram client.

    This must be called before accessing bot or client.
    Creates instances and logs in the bot, but does NOT connect it
    (use bot.connect() separately to start the event loop).

    Raises RuntimeError if called more than once.
    Raises ValueError or RuntimeError if initialization fails.
    """
    global _bot, _client

    if _bot is not None or _client is not None:
        raise RuntimeError("Services have already been initialized")

    # Initialize bot and Telegram client in parallel
    async def init_bot() -> Bot:
        try:
            return await Bot.create_and_initialize(config.discord_token)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Discord bot: {e}") from e

    async def init_client() -> TelegramClientManager:
        try:
            return await TelegramClientManager.create_and_connect(
                api_id=config.telegram_api_id,
                api_hash=config.telegram_api_hash,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Telegram client: {e}") from e

    try:
        _bot, _client = await asyncio.gather(init_bot(), init_client())
    except Exception:
        _bot = None
        _client = None
        raise
