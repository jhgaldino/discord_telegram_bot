import logging
import sqlite3

import discord
import telethon.errors
from discord import app_commands
from discord.ext import commands
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.types import Channel as TelegramChannel
from telethon.utils import get_input_channel

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

    discord_group = app_commands.Group(
        name="discord", description="Comandos para gerenciar canais do Discord"
    )

    @staticmethod
    def _get_telegram_url_markdown(username: str) -> str:
        return f"[{username}](https://t.me/{username})"

    @discord_group.command(name="adicionar", description="Adiciona um canal do Discord")
    @app_commands.describe(canal="ID do canal do Discord")
    @admin_only()
    async def add_discord(
        self, interaction: discord.Interaction, canal: discord.abc.GuildChannel
    ) -> None:
        bot_member = canal.guild.get_member(interaction.application_id)
        if bot_member and not canal.permissions_for(bot_member).send_messages:
            await interaction.response.send_message(
                f"Não tenho permissão para enviar mensagens em {canal.mention}"
            )
            return

        try:
            channel_db.add_discord_channel(canal.id)
            services.forwarder.reload_channels()
            await interaction.response.send_message(
                f"Adicionei o canal do Discord {canal.mention}"
            )
        except ChannelAlreadyExistsError:
            await interaction.response.send_message(
                f"O canal {canal.mention} já está na lista"
            )
        except sqlite3.DatabaseError as e:
            logger.error(f"Database error adding Discord channel: {e}", exc_info=e)
            await interaction.response.send_message(
                "Erro ao adicionar o canal. Tente novamente."
            )

    @discord_group.command(name="remover", description="Remove um canal do Discord")
    @app_commands.describe(canal="ID do canal do Discord")
    @admin_only()
    async def remove_discord(
        self, interaction: discord.Interaction, canal: discord.abc.GuildChannel
    ) -> None:
        try:
            channel_db.remove_discord_channel(canal.id)
            services.forwarder.reload_channels()
            await interaction.response.send_message(
                f"Removi o canal do Discord {canal.mention}"
            )
        except ChannelNotFoundError:
            await interaction.response.send_message(
                f"O canal {canal.mention} não está na lista"
            )
        except sqlite3.DatabaseError as e:
            logger.error(f"Database error removing Discord channel: {e}", exc_info=e)
            await interaction.response.send_message(
                "Erro ao remover o canal. Tente novamente."
            )

    @discord_group.command(
        name="listar", description="Lista todos os canais do Discord"
    )
    @admin_only()
    async def list_discord(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        channel_list = channel_db.list_discord_channels()

        if not channel_list:
            await interaction.followup.send("Não há canais do Discord configurados")
            return

        message_parts: list[str] = []
        for channel in channel_list:
            message_parts.append(f"- <#{channel.channel_id}>")

        header = (
            f"Você tem {len(channel_list)} canal(is) do Discord configurado(s):\n\n"
        )
        message = header + "\n".join(message_parts)

        await interaction.followup.send(message)

    telegram_group = app_commands.Group(
        name="telegram", description="Comandos para gerenciar canais do Telegram"
    )

    @telegram_group.command(
        name="adicionar", description="Adiciona um canal do Telegram"
    )
    @app_commands.describe(
        canal="Link, Username ou ID do canal do Telegram",
        encaminhar="Se o canal deve encaminhar mensagens para o Discord (padrão: True)",
    )
    @admin_only()
    async def add_telegram(
        self, interaction: discord.Interaction, canal: str, encaminhar: bool = True
    ) -> None:
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

        # Join channel if not already joined, archive it to keep it hidden
        if channel.left:
            input_channel = get_input_channel(channel)
            try:
                await services.client(JoinChannelRequest(input_channel))
                await services.client.edit_folder(input_channel, 1)
            except (
                telethon.errors.RPCError,
                ConnectionError,
                TimeoutError,
            ) as e:
                logger.warning(f"Failed to join Telegram channel: {e}", exc_info=e)
                await interaction.response.send_message(
                    "Não foi possível entrar no canal, tente novamente mais tarde."
                )
                return

        channel_url = self._get_telegram_url_markdown(username)

        try:
            channel_db.add_telegram_channel(channel.id, username, encaminhar)
            services.forwarder.reload_channels()
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
            services.forwarder.reload_channels()

            # Leave channel if joined
            if not channel.left:
                input_channel = get_input_channel(channel)
                try:
                    await services.client(LeaveChannelRequest(input_channel))
                except (
                    telethon.errors.RPCError,
                    ConnectionError,
                    TimeoutError,
                ) as e:
                    logger.warning(f"Error leaving Telegram channel: {e}", exc_info=e)

            await interaction.response.send_message(
                f"Removi o canal do Telegram {channel_url}",
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
