import logging
from typing import Optional

import aiohttp

import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import MISSING
from src.services.discord.cog_loader import CogLoader


class Bot(commands.Bot):
    """Custom Bot class for Discord bot functionality."""

    def __init__(self) -> None:
        """Initialize the bot."""
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix="🝍",
            intents=intents,
        )

        self.logger = logging.getLogger(self.__class__.__name__)
        self._session: aiohttp.ClientSession | None = None
        self._loader: CogLoader | None = None
        self._logged_in: bool = False

    @classmethod
    async def create_and_initialize(cls, token: str) -> "Bot":
        """
        Create and initialize a Bot instance by logging in.

        Raises ValueError if token is invalid.
        Raises RuntimeError if initialization fails.
        """
        if not token:
            raise ValueError("Discord token is required")

        bot = cls()
        try:
            await bot.login(token)
            bot._logged_in = True
            bot.logger.info("Discord bot initialized and logged in")
            return bot
        except Exception as e:
            bot.logger.error(f"Failed to initialize Discord bot: {e}")
            raise RuntimeError(f"Failed to initialize Discord bot: {e}") from e

    async def _send_interaction_message(
        self, interaction: discord.Interaction, message: str, ephemeral: bool = True
    ) -> None:
        """Helper to send a message to an interaction, handling response state."""
        if interaction.response.is_done():
            try:
                await interaction.followup.send(message, ephemeral=ephemeral)
            except Exception:
                pass
        else:
            try:
                await interaction.response.send_message(message, ephemeral=ephemeral)
            except Exception:
                pass

    async def setup_hook(self) -> None:
        """Called when the bot is starting up."""
        # Create aiohttp session
        self._session = aiohttp.ClientSession()

        # Set up tree error handler to catch CommandNotFound early
        @self.tree.error
        async def on_tree_error(
            interaction: discord.Interaction, error: app_commands.AppCommandError
        ) -> None:
            if isinstance(error, app_commands.CommandNotFound):
                await self._send_interaction_message(
                    interaction,
                    "Este comando está temporariamente indisponível. Por favor, tente novamente em um momento.",
                )
                return
            await self.on_app_command_error(interaction, error)

        self._loader = CogLoader(bot=self, hot_reload=True)
        await self._loader.start()

    async def on_ready(self) -> None:
        """Called when the bot is ready."""
        self.logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        self.logger.info(f"Connected to {len(self.guilds)} guild(s)")
        self.logger.info("Automatic hot-reload is enabled for the 'cogs' directory")

        synced = await self.tree.sync()
        self.logger.info(f"Synced {len(synced)} command(s)")

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        """Global error handler for prefix commands."""
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Bad argument: {error}")
        else:
            self.logger.error(f"Unhandled error: {error}", exc_info=error)
            await ctx.send(f"An error occurred: {error}")

    async def on_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        """Global error handler for slash commands."""
        if isinstance(error, app_commands.MissingPermissions):
            await self._send_interaction_message(
                interaction, "You don't have permission to use this command."
            )
        elif isinstance(error, app_commands.CommandOnCooldown):
            await self._send_interaction_message(
                interaction,
                f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds.",
            )
        else:
            self.logger.error(f"Unhandled app command error: {error}", exc_info=error)
            await self._send_interaction_message(
                interaction, f"An error occurred: {error}"
            )

    async def close(self) -> None:
        """Clean up resources when the bot is closing."""
        if self._loader:
            await self._loader.stop()

        if self._session:
            await self._session.close()
        await super().close()

    def run(
        self,
        token: str,
        *,
        reconnect: bool = True,
        log_handler: Optional[logging.Handler] = MISSING,
        log_formatter: logging.Formatter = MISSING,
        log_level: int = MISSING,
        root_logger: bool = False,
    ) -> None:
        """
        Run the bot.

        Args:
            token: Discord bot token
        """

        # Disable discord.py's default logging to avoid duplicating logs
        super().run(
            token,
            reconnect=reconnect,
            log_handler=None,
        )
