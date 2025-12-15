"""Reminders cog - Commands for managing reminders."""

import discord
from discord import app_commands
from discord.ext import commands

from src.database import reminders
from src.shared.utils import format_list_to_markdown, plural


class Reminders(
    commands.GroupCog,
    name="lembretes",
    description="Gerenciamento de lembretes",
):
    """A cog for reminder commands."""

    def __init__(self) -> None:
        pass

    @app_commands.command(
        name="adicionar",
        description="Peça para o bot te lembrar quando encontrar um texto específico",
    )
    async def add_reminder(
        self, interaction: discord.Interaction, lembrete: str
    ) -> None:
        """Add a reminder."""
        reminders.add_reminder(interaction.user.id, lembrete)
        await interaction.response.send_message(
            f"Vou te lembrar quando encontrar **{lembrete}**"
        )

    @app_commands.command(
        name="listar",
        description="Mostra os lembretes que o bot está guardando pra você",
    )
    async def list_reminders(self, interaction: discord.Interaction) -> None:
        """List all reminders for the user."""
        reminder_list = reminders.get_user_reminders(interaction.user.id)
        if not reminder_list:
            await interaction.response.send_message(
                "Você não tem nenhum lembrete guardado"
            )
            return

        markdown_list = format_list_to_markdown(reminder_list)
        quant = len(reminder_list)
        message = f"Você tem {quant} lembrete{plural(quant, '', 's')} guardado{plural(quant, '', 's')}:\n{markdown_list}"
        await interaction.response.send_message(message)

    @app_commands.command(name="remover", description="Remove um lembrete da lista")
    async def remove_reminder(
        self, interaction: discord.Interaction, lembrete: str
    ) -> None:
        """Remove a reminder."""
        reminders.remove_reminder(interaction.user.id, lembrete)
        await interaction.response.send_message(
            f"Não vou mais te lembrar de **{lembrete}**"
        )


async def setup(bot: commands.Bot) -> None:
    """Setup function to add the cog to the bot."""
    await bot.add_cog(Reminders())
