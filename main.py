import asyncio
import logging
import sys
from contextlib import suppress

import discord.utils

from src.config import config
from src.services.discord.bot import Bot
from src.services.forwarder.forwarder import MessageForwarder
from src.services.telegram.client import TelegramClient
from src.shared.exceptions import ServiceNotInitializedError
from src.shared.services import services

# Configure logging based on environment
log_level = logging.INFO if config.is_development else logging.WARNING
discord.utils.setup_logging(level=log_level)

logger = logging.getLogger(__name__)


async def initialize_services() -> None:
    """Initialize all services: Discord bot, Telegram client, and message forwarder."""
    bot, client = await asyncio.gather(
        Bot.create_and_initialize(config.discord_token),
        TelegramClient.create_and_connect(
            api_id=config.telegram_api_id,
            api_hash=config.telegram_api_hash,
        ),
    )
    services.bot = bot
    services.client = client

    # Setup forwarder (main application functionality)
    forwarder = MessageForwarder()
    forwarder.start()
    services.forwarder = forwarder

    async def on_ready_handler() -> None:
        await forwarder.on_bot_ready()

    services.bot.add_listener(on_ready_handler, "on_ready")


async def cleanup_services() -> None:
    """Cleanup all services gracefully, ignoring errors if services aren't initialized."""

    async def cleanup_bot() -> None:
        with suppress(ServiceNotInitializedError, AssertionError):
            await services.bot.close()

    async def cleanup_client() -> None:
        with suppress(ServiceNotInitializedError, AssertionError):
            await services.client.disconnect()

    await asyncio.gather(cleanup_bot(), cleanup_client(), return_exceptions=True)


async def run_services() -> None:
    try:
        await initialize_services()
        await services.bot.connect()  # Blocks until the bot is closed
    finally:
        await cleanup_services()


def main() -> None:
    try:
        logger.info("Starting application...")
        asyncio.run(run_services())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=e)
        sys.exit(1)


if __name__ == "__main__":
    main()
