import logging

import discord
from discord import app_commands
from discord.ext import commands
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.types import Channel as TelegramChannel
from telethon.utils import get_input_channel

from src.config import get_client, get_forwarder
from src.database import channels as channel_db
from src.shared.permissions import admin_only
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

        success, error = channel_db.add_discord_channel(canal.id)

        if success:
            get_forwarder().reload_channels()

            await interaction.response.send_message(
                f"Adicionei o canal do Discord {canal.mention}"
            )
        elif error == "already_exists":
            await interaction.response.send_message(
                f"O canal {canal.mention} já está na lista"
            )
        else:
            await interaction.response.send_message(
                "Erro ao adicionar o canal. Tente novamente."
            )

    @discord_group.command(name="remover", description="Remove um canal do Discord")
    @app_commands.describe(canal="ID do canal do Discord")
    @admin_only()
    async def remove_discord(
        self, interaction: discord.Interaction, canal: discord.abc.GuildChannel
    ) -> None:
        success, error = channel_db.remove_discord_channel(canal.id)

        if success:
            get_forwarder().reload_channels()

            await interaction.response.send_message(
                f"Removi o canal do Discord {canal.mention}"
            )
        elif error == "not_found":
            await interaction.response.send_message(
                f"O canal {canal.mention} não está na lista"
            )
        else:
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
        telegram = get_client().client
        channel = await telegram.get_entity(canal)
        if not isinstance(channel, TelegramChannel):
            await interaction.response.send_message(
                f"**{canal}** não é um canal", suppress_embeds=True
            )
            return

        # Check if channel is public
        username = channel.username
        if not username:
            await interaction.response.send_message(
                f"Apenas canais públicos podem ser adicionados."
            )
            return

        # Join channel if not already joined
        if channel.left:
            input_channel = get_input_channel(channel)
            try:
                await telegram(JoinChannelRequest(input_channel))
                await telegram.edit_folder(
                    input_channel, 1
                )  # Archive channel to keep it hidden
            except Exception as e:
                await interaction.response.send_message(
                    f"Não foi possível entrar no canal, tente novamente mais tarde."
                )
                return

        success, error = channel_db.add_telegram_channel(
            channel.id, username, encaminhar
        )
        channel_url = self._get_telegram_url_markdown(username)

        if success:
            get_forwarder().reload_channels()

            await interaction.response.send_message(
                f"Adicionei o canal do Telegram {channel_url}",
                suppress_embeds=True,
            )
        elif error == "already_exists":
            await interaction.response.send_message(
                f"O canal {channel_url} já está na lista",
                suppress_embeds=True,
            )
        else:
            await interaction.response.send_message(
                "Erro ao adicionar o canal. Tente novamente."
            )

    @telegram_group.command(name="remover", description="Remove um canal do Telegram")
    @app_commands.describe(canal="Link, Username ou ID do canal do Telegram")
    @admin_only()
    async def remove_telegram(
        self, interaction: discord.Interaction, canal: str
    ) -> None:
        telegram = get_client().client
        channel = await telegram.get_entity(canal)
        if not isinstance(channel, TelegramChannel):
            await interaction.response.send_message(
                f"**{canal}** não é um canal", suppress_embeds=True
            )
            return

        # Check if channel exists in database first
        success, error = channel_db.remove_telegram_channel(channel.id)

        if error == "not_found":
            escaped_channel = self._escape_channel(canal)
            await interaction.response.send_message(
                f"O canal **{escaped_channel}** não está na lista", suppress_embeds=True
            )
            return

        if not success:
            await interaction.response.send_message(
                "Erro ao remover o canal. Tente novamente."
            )
            return

        get_forwarder().reload_channels()

        # Leave channel if joined
        if not channel.left:
            input_channel = get_input_channel(channel)
            try:
                await telegram(LeaveChannelRequest(input_channel))
            except Exception as e:
                logger.warning(f"Error leaving Telegram channel", exc_info=e)

        # Use username if available, otherwise use escaped channel identifier
        username = channel.username
        if username:
            channel_url = self._get_telegram_url_markdown(username)
        else:
            channel_url = f"**{self._escape_channel(canal)}**"

        await interaction.response.send_message(
            f"Removi o canal do Telegram {channel_url}",
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
