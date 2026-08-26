import platform
import sys

import discord
from discord import app_commands
from discord.ext import commands

from src.shared.permissions import admin_only
from src.shared.services import services


class Info(commands.Cog):
    def __init__(self) -> None:
        self.start_time = discord.utils.utcnow()

    @app_commands.command(name="info", description="Mostra informações sobre o bot")
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


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Info())
