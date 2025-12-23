import platform
import sys

import discord
from discord import app_commands
from discord.ext import commands

from src.services.telegram.exceptions import AUTH_ERRORS
from src.shared.permissions import admin_only
from src.shared.services import services


class Info(commands.GroupCog, name="info", description="Bot information commands"):
    def __init__(self) -> None:
        self.start_time = discord.utils.utcnow()

    @app_commands.command(name="bot", description="Mostra informações sobre o bot")
    @admin_only()
    async def info(self, interaction: discord.Interaction) -> None:
        uptime = discord.utils.utcnow() - self.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        embed = discord.Embed(
            title="Informações do Bot",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="Nome do Bot", value=services.bot.user.name, inline=True)
        embed.add_field(name="ID do Bot", value=services.bot.user.id, inline=True)
        embed.add_field(
            name="Latência",
            value=f"{round(services.bot.latency * 1000)}ms",
            inline=True,
        )
        embed.add_field(name="Servidores", value=len(services.bot.guilds), inline=True)
        embed.add_field(name="Usuários", value=len(services.bot.users), inline=True)
        embed.add_field(
            name="Tempo Online",
            value=f"{days}d {hours}h {minutes}m {seconds}s",
            inline=True,
        )
        embed.add_field(
            name="Versão do Python", value=sys.version.split()[0], inline=True
        )
        embed.add_field(
            name="Versão do discord.py", value=discord.__version__, inline=True
        )
        embed.add_field(name="Plataforma", value=platform.system(), inline=True)
        embed.set_thumbnail(url=services.bot.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="telegram", description="Mostra informações sobre o Telegram"
    )
    @admin_only()
    async def telegram(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        # Telegram connection status
        is_connected = services.client.is_connected()
        if not is_connected:
            await interaction.followup.send(
                "❌ **Telegram:** Desconectado", ephemeral=True
            )
            return

        status_lines: list[str] = []
        status_lines.append("✅ **Telegram:** Conectado")

        # Check authentication
        try:
            me = await services.client.get_me()
            if not me:
                status_lines.append(
                    "❌ **Autenticação:** Não autenticado (use `/telegram login`)"
                )
            else:
                status_lines.append(
                    f"✅ **Autenticação:** Logado como **{me.first_name}** (@{me.username})"
                )
        except AUTH_ERRORS as e:
            status_lines.append(f"❌ **Autenticação:** Erro - {str(e)}")
        except (ConnectionError, TimeoutError) as e:
            status_lines.append(f"⚠️ **Autenticação:** Erro ao verificar - {str(e)}")

        message = "\n".join(status_lines)
        await interaction.followup.send(message, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Info())
