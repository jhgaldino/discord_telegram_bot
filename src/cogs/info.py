"""Info cog - Bot information commands."""

import platform
import sys
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from src.config import get_bot, get_client
from src.services.telegram.errors import AUTH_ERRORS


class Info(commands.GroupCog, name="info", description="Bot information commands"):
    """A cog for bot information commands."""

    def __init__(self) -> None:
        self.start_time = datetime.now(timezone.utc)

    @app_commands.command(name="info", description="Display bot information")
    async def info(self, interaction: discord.Interaction) -> None:
        """Display bot information."""
        uptime = datetime.now(timezone.utc) - self.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        embed = discord.Embed(
            title="Bot Information",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc),
        )
        bot = get_bot()
        embed.add_field(name="Bot Name", value=bot.user.name, inline=True)
        embed.add_field(name="Bot ID", value=bot.user.id, inline=True)
        embed.add_field(name="Servers", value=len(bot.guilds), inline=True)
        embed.add_field(name="Users", value=len(bot.users), inline=True)
        embed.add_field(
            name="Uptime",
            value=f"{days}d {hours}h {minutes}m {seconds}s",
            inline=True,
        )
        embed.add_field(
            name="Python Version", value=sys.version.split()[0], inline=True
        )
        embed.add_field(
            name="discord.py Version", value=discord.__version__, inline=True
        )
        embed.add_field(name="Platform", value=platform.system(), inline=True)
        embed.set_thumbnail(url=bot.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="Display server information")
    async def serverinfo(self, interaction: discord.Interaction) -> None:
        """Display server information."""
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"{guild.name} Information",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(name="Server Name", value=guild.name, inline=True)
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(
            name="Owner",
            value=guild.owner.mention if guild.owner else "Unknown",
            inline=True,
        )
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(
            name="Channels",
            value=len(guild.channels),
            inline=True,
        )
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(
            name="Created",
            value=guild.created_at.strftime("%Y-%m-%d"),
            inline=True,
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="status", description="Mostra vários status do bot")
    async def status(self, interaction: discord.Interaction) -> None:
        """Show bot status including Telegram connection."""
        # Check if user is bot owner
        if not self._is_owner(interaction):
            await interaction.response.send_message(
                "Você não tem permissão para usar este comando.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        status_lines = []

        bot = get_bot()
        telegram_manager = get_client()

        # Discord bot status
        status_lines.append(f"📊 **Latência:** {round(bot.latency * 1000)}ms")
        status_lines.append("✅ **Discord Bot:** Online")

        # Telegram connection status
        try:
            is_connected = telegram_manager.is_connected()
            if is_connected:
                status_lines.append("✅ **Telegram:** Conectado")

                # Check authentication
                try:
                    is_authorized = await telegram_manager.is_user_authorized()
                    if is_authorized:
                        me = await telegram_manager.client.get_me()
                        status_lines.append(
                            f"✅ **Autenticação:** Logado como **{me.first_name}** (@{me.username})"
                        )
                    else:
                        status_lines.append(
                            "❌ **Autenticação:** Não autenticado (use `/telegram login`)"
                        )
                except AUTH_ERRORS as e:
                    status_lines.append(f"❌ **Autenticação:** Erro - {str(e)}")
                except Exception as e:
                    status_lines.append(
                        f"⚠️ **Autenticação:** Erro ao verificar - {str(e)}"
                    )
            else:
                status_lines.append("❌ **Telegram:** Desconectado")
        except Exception as e:
            status_lines.append(
                f"❌ **Telegram:** Erro ao verificar conexão - {str(e)}"
            )

        message = "\n".join(status_lines)
        await interaction.followup.send(message, ephemeral=True)

    def _is_owner(self, interaction: discord.Interaction) -> bool:
        """Check if the user is the bot owner."""
        bot = get_bot()
        if bot.owner_id:
            return interaction.user.id == bot.owner_id
        # Fallback: check application owners
        app = interaction.client.application
        if app and app.owner:
            if isinstance(app.owner, discord.Team):
                return interaction.user.id in [
                    member.id for member in app.owner.members
                ]
            return interaction.user.id == app.owner.id
        return False


async def setup(bot: commands.Bot) -> None:
    """Setup function to add the cog to the bot."""
    await bot.add_cog(Info())
