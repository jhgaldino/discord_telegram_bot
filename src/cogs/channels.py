import logging
import sqlite3

import discord
import telethon.errors
from discord import app_commands
from discord.ext import commands
from telethon.tl.types import Channel as TelegramChannel

from src.database import channels as channel_db
from src.shared.exceptions import (
    ChannelAlreadyExistsError,
    ChannelNotFoundError,
)
from src.shared.permissions import admin_only
from src.shared.services import services
from src.shared.utils import plural

logger = logging.getLogger(__name__)


class Channels(commands.GroupCog, name="canais", description="Gerenciamento de canais"):
    def __init__(self) -> None:
        pass

    @staticmethod
    def _escape_channel(channel: str | int) -> str:
        return discord.utils.escape_markdown(str(channel))

    @staticmethod
    def _get_telegram_url_markdown(username: str) -> str:
        return f"[{username}](https://t.me/{username})"

    telegram_group = app_commands.Group(
        name="telegram", description="Comandos para gerenciar canais do Telegram"
    )

    @telegram_group.command(
        name="adicionar", description="Adiciona um canal do Telegram"
    )
    @app_commands.describe(canal="Link, Username ou ID do canal do Telegram")
    @admin_only()
    async def add_telegram(self, interaction: discord.Interaction, canal: str) -> None:
        channel = await services.client.get_entity(canal)
        if not isinstance(channel, TelegramChannel):
            await interaction.response.send_message(
                f"**{canal}** não é um canal", suppress_embeds=True
            )
            return

        # Check if channel is public
        username = channel.username
        if not username:
            await interaction.response.send_message(
                "Apenas canais públicos podem ser adicionados."
            )
            return

        try:
            await services.client.ensure_channel_subscription(channel)
        except (
            telethon.errors.RPCError,
            ConnectionError,
            TimeoutError,
            ValueError,
        ) as e:
            logger.warning(
                f"Failed to configure Telegram channel subscription: {e}",
                exc_info=e,
            )
            await interaction.response.send_message(
                "Não foi possível configurar o canal no Telegram, tente novamente mais tarde."
            )
            return

        channel_url = self._get_telegram_url_markdown(username)

        try:
            channel_db.add_telegram_channel(channel.id, username)
            services.notifier.reload_channels()
            await interaction.response.send_message(
                f"Adicionei o canal do Telegram {channel_url}",
                suppress_embeds=True,
            )
        except ChannelAlreadyExistsError:
            await interaction.response.send_message(
                f"O canal {channel_url} já está na lista",
                suppress_embeds=True,
            )
        except sqlite3.DatabaseError as e:
            logger.error(f"Database error adding Telegram channel: {e}", exc_info=e)
            await interaction.response.send_message(
                "Erro ao adicionar o canal. Tente novamente.",
            )

    @telegram_group.command(name="remover", description="Remove um canal do Telegram")
    @app_commands.describe(canal="Link, Username ou ID do canal do Telegram")
    @admin_only()
    async def remove_telegram(
        self, interaction: discord.Interaction, canal: str
    ) -> None:
        channel = await services.client.get_entity(canal)
        if not isinstance(channel, TelegramChannel):
            await interaction.response.send_message(
                f"**{canal}** não é um canal", suppress_embeds=True
            )
            return

        # Use username if available, otherwise use escaped channel identifier
        username = channel.username
        if username:
            channel_url = self._get_telegram_url_markdown(username)
        else:
            escaped_channel = self._escape_channel(canal)
            channel_url = f"**{escaped_channel}**"

        try:
            channel_db.remove_telegram_channel(channel.id)
            services.notifier.reload_channels()

            await interaction.response.send_message(
                f"Parei de monitorar o canal do Telegram {channel_url}",
                suppress_embeds=True,
            )
        except ChannelNotFoundError:
            await interaction.response.send_message(
                f"O canal {channel_url} não está na lista", suppress_embeds=True
            )
        except sqlite3.DatabaseError as e:
            logger.error(f"Database error removing Telegram channel: {e}", exc_info=e)
            await interaction.response.send_message(
                "Erro ao remover o canal. Tente novamente.",
                suppress_embeds=True,
            )

    @telegram_group.command(
        name="listar", description="Lista todos os canais do Telegram"
    )
    @admin_only()
    async def list_telegram(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        channel_list = channel_db.list_telegram_channels()

        if not channel_list:
            await interaction.followup.send("Não há canais do Telegram configurados")
            return

        message_parts: list[str] = []
        for channel in channel_list:
            channel_url = self._get_telegram_url_markdown(channel.username)
            message_parts.append(f"- {channel_url}")

        channel_plural = plural(len(channel_list), "canal", "canais")
        header = f"Você tem {len(channel_list)} {channel_plural} do Telegram configurado(s):\n\n"
        message = header + "\n".join(message_parts)

        await interaction.followup.send(message, suppress_embeds=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Channels())
