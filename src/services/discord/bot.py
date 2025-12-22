import logging
from typing import Optional

import aiohttp

import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import MISSING
from src.services.discord.cog_loader import CogLoader


class Bot(commands.Bot):
    def __init__(self) -> None:
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

        synced = await self.tree.sync()
        self.logger.info(f"Synced {len(synced)} command(s)")

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        """Global error handler for prefix commands."""
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Argumento obrigatório: {error.param.name}")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"Argumento inválido: {error}")
        else:
            self.logger.error(f"Unhandled command error: {error}", exc_info=error)
            await ctx.send(f"Ocorreu um erro ao executar o comando.")

    async def on_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        """Global error handler for slash commands."""
        if isinstance(
            error, (app_commands.MissingPermissions, app_commands.CheckFailure)
        ):
            await self._send_interaction_message(
                interaction, "Você não tem permissão para usar este comando."
            )
        elif isinstance(error, app_commands.CommandOnCooldown):
            await self._send_interaction_message(
                interaction,
                f"Este comando está em cooldown. Tente novamente em {error.retry_after:.2f} segundos.",
            )
        else:
            self.logger.error(f"Unhandled app command error: {error}", exc_info=error)
            await self._send_interaction_message(
                interaction, f"Ocorreu um erro ao executar o comando."
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
        # Disable discord.py's default logging to avoid duplicating logs
        super().run(
            token,
            reconnect=reconnect,
            log_handler=None,
        )
