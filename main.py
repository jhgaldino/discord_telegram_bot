"""Main entrypoint for the Discord-Telegram bot."""

import asyncio
import logging
import sys

import discord.utils

from src.config import config, get_bot, get_client
from src.config import initialize as initialize_services
from src.services.integration.forwarder import MessageForwarder

# Configure our own logger to look like the discord.py logger because it's cool
discord.utils.setup_logging(level=logging.INFO)

logger = logging.getLogger(__name__)


async def setup_forwarder() -> MessageForwarder:
    """Setup message forwarder after services are initialized."""
    forwarder = MessageForwarder(
        telegram_channels=config.telegram_channels,
        discord_channel_ids=config.discord_channel_ids,
    )
    forwarder.start()

    bot = get_bot()

    async def on_ready_handler() -> None:
        await forwarder.on_bot_ready()

    bot.add_listener(on_ready_handler, "on_ready")
    return forwarder


async def cleanup_services() -> None:
    """Cleanup Discord bot and Telegram client."""

    async def cleanup_bot() -> None:
        try:
            bot = get_bot()
            await bot.close()
        except RuntimeError:
            pass
        except Exception as e:
            logger.error(f"Error closing bot: {e}", exc_info=e)

    async def cleanup_client() -> None:
        try:
            telegram_client = get_client()
            await telegram_client.disconnect()
        except RuntimeError:
            pass
        except Exception as e:
            logger.error(f"Error disconnecting Telegram client: {e}", exc_info=e)

    await asyncio.gather(cleanup_bot(), cleanup_client(), return_exceptions=True)


async def run_services() -> None:
    """Run both Discord bot and Telegram client independently."""
    try:
        await initialize_services()
        await setup_forwarder()

        bot = get_bot()
        await bot.connect()  # Blocks until the bot is closed
    finally:
        await cleanup_services()


def main() -> None:
    """Main entrypoint."""
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
