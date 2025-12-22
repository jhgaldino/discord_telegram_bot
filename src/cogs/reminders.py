import discord
from discord import app_commands
from discord.ext import commands

from src.database import reminders
from src.database.reminders import (
    ERROR_ALREADY_EXISTS,
    ERROR_LIMIT_REACHED,
    ERROR_TEXT_EXISTS,
    MAX_GROUPS_PER_USER,
    MAX_TEXTS_PER_GROUP,
)
from src.shared.utils import (
    format_list_to_markdown,
    plural,
    sanitize_text,
)


class Reminders(
    commands.GroupCog,
    name="lembretes",
    description="Gerenciamento de lembretes",
):
    def __init__(self) -> None:
        pass

    @staticmethod
    def _resolve_group_name(group: str | None, text: str) -> str:
        return group if group is not None else text

    @staticmethod
    def _sanitize_and_escape_text(text: str) -> str:
        return discord.utils.escape_markdown(sanitize_text(text))

    @staticmethod
    def _escape_group(group: str) -> str:
        return discord.utils.escape_markdown(group)

    @app_commands.command(
        name="adicionar",
        description="Adiciona um texto a um grupo de lembretes",
    )
    @app_commands.describe(
        texto="Texto para adicionar ao grupo",
        grupo="Nome do grupo (opcional, se não especificado cria um grupo com o nome do texto)",
    )
    async def add_text(
        self,
        interaction: discord.Interaction,
        texto: str,
        grupo: str | None = None,
    ) -> None:
        # If no group specified, use the text name as group name (preserving casing)
        grupo = self._resolve_group_name(grupo, texto)

        # Try to ensure group exists
        _, create_error = reminders.create_group(interaction.user.id, grupo)
        if create_error == ERROR_LIMIT_REACHED:
            await interaction.response.send_message(
                f"Você já tem {MAX_GROUPS_PER_USER} grupos de lembretes. "
                "Delete um grupo antes de criar outro."
            )
            return
        # If group doesn't exist and wasn't created, it's an error
        if create_error and create_error != ERROR_ALREADY_EXISTS:
            await interaction.response.send_message(
                "Erro ao criar o grupo. Tente novamente."
            )
            return

        success, add_error = reminders.add_text_to_group(
            interaction.user.id, grupo, texto
        )

        escaped_text = self._sanitize_and_escape_text(texto)
        escaped_group = self._escape_group(grupo)

        if not success:
            if add_error == ERROR_LIMIT_REACHED:
                await interaction.response.send_message(
                    f"O grupo **{escaped_group}** já tem {MAX_TEXTS_PER_GROUP} textos. "
                    "Remova um texto antes de adicionar outro."
                )
                return
            if add_error == ERROR_TEXT_EXISTS:
                await interaction.response.send_message(
                    f"O texto **{escaped_text}** já existe no grupo **{escaped_group}**"
                )
                return
            await interaction.response.send_message(
                f"O grupo **{escaped_group}** não existe"
            )
            return

        # Success case
        if grupo == texto:
            # Auto-created group with text name
            await interaction.response.send_message(
                f"Vou te lembrar quando encontrar **{escaped_text}**"
            )
            return

        # Explicit group specified
        await interaction.response.send_message(
            f"Adicionei **{escaped_text}** ao grupo **{escaped_group}**"
        )

    @app_commands.command(
        name="listar",
        description="Mostra grupos de lembretes e seus textos",
    )
    @app_commands.describe(
        grupo="Nome do grupo (opcional, se não especificado mostra todos os grupos)",
    )
    async def list_groups(
        self, interaction: discord.Interaction, grupo: str | None = None
    ) -> None:
        # Defer response immediately to prevent interaction timeout
        await interaction.response.defer()

        groups = reminders.list_groups_by_user(interaction.user.id, grupo)

        if not groups:
            if grupo:
                escaped_group = self._escape_group(grupo)
                await interaction.followup.send(
                    f"O grupo **{escaped_group}** não existe"
                )
            else:
                await interaction.followup.send(
                    "Você não tem nenhum grupo de lembretes"
                )
            return

        message_parts: list[str] = []
        for group in groups:
            escaped_group = self._escape_group(group.group_name)
            texts = group.texts
            if not texts:
                message_parts.append(f"**{escaped_group}:** *(vazio)*")
                continue

            escaped_texts = [self._sanitize_and_escape_text(text) for text in texts]
            texts_list = format_list_to_markdown(escaped_texts)
            message_parts.append(f"**{escaped_group}:**\n{texts_list}")

        if grupo:
            # Single group listing
            message = "\n\n".join(message_parts)
        else:
            # All groups listing
            total_groups = len(groups)
            groups_plural = plural(total_groups, "grupo", "grupos")
            header = f"Você tem {total_groups} {groups_plural} de lembretes:\n\n"
            message = header + "\n\n".join(message_parts)

        await interaction.followup.send(message)

    @app_commands.command(
        name="remover",
        description="Remove um texto de um grupo de lembretes",
    )
    @app_commands.describe(
        texto="Texto para remover do grupo",
        grupo="Nome do grupo (opcional, se não especificado usa o nome do texto)",
    )
    async def remove_text(
        self,
        interaction: discord.Interaction,
        texto: str,
        grupo: str | None = None,
    ) -> None:
        # If no group specified, use the text name as group name
        group_name = self._resolve_group_name(grupo, texto)
        success, _, group_deleted = reminders.remove_text_from_group(
            interaction.user.id, group_name, texto
        )

        escaped_text = self._sanitize_and_escape_text(texto)
        escaped_group = self._escape_group(group_name)

        if not success:
            await interaction.response.send_message(
                f"O grupo **{escaped_group}** não existe ou o texto **{escaped_text}** não está nele"
            )
            return

        message = f"Removi **{escaped_text}** do grupo **{escaped_group}**"
        if group_deleted:
            message += ". O grupo foi deletado por estar vazio."
        await interaction.response.send_message(message)

    @app_commands.command(
        name="deletar",
        description="Deleta um grupo de lembretes e todos os seus textos",
    )
    @app_commands.describe(grupo="Nome do grupo a deletar")
    async def delete_group(self, interaction: discord.Interaction, grupo: str) -> None:
        success, _ = reminders.delete_group(interaction.user.id, grupo)

        escaped_group = self._escape_group(grupo)

        if not success:
            await interaction.response.send_message(
                f"O grupo **{escaped_group}** não existe"
            )
            return

        await interaction.response.send_message(
            f"Deletei o grupo **{escaped_group}** e todos os seus textos"
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Reminders())
