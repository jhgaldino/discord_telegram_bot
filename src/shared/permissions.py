from collections.abc import Callable
from typing import Any

from discord import Interaction, app_commands


def admin_only() -> Callable[[Callable[..., Any]], Any]:
    """
    Restrict a command to bot team members or owner only.
    """

    def is_bot_admin(interaction: Interaction) -> bool:
        app = interaction.client.application
        if app:
            if app.team:
                for member in app.team.members:
                    if member.id == interaction.user.id:
                        return True
            return app.owner.id == interaction.user.id
        return False

    return app_commands.check(is_bot_admin)
