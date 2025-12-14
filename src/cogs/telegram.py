"""Telegram cog - Telegram configuration and login commands."""

import asyncio
import datetime

import discord
from discord import app_commands
from discord.ext import commands

from src.config import get_bot, get_client
from src.services.telegram import qr as telegram
from src.services.telegram.errors import AUTH_ERRORS, PASSWORD_ERRORS, TIMEOUT_ERRORS


def is_owner(bot: commands.Bot, interaction: discord.Interaction) -> bool:
    """Check if the user is the bot owner."""
    if bot.owner_id:
        return interaction.user.id == bot.owner_id
    # Fallback: check application owners
    app = interaction.client.application
    if app and app.owner:
        if isinstance(app.owner, discord.Team):
            return interaction.user.id in [member.id for member in app.owner.members]
        return interaction.user.id == app.owner.id
    return False


class Telegram(
    commands.GroupCog, name="telegram", description="Telegram configuration commands"
):
    """A cog for Telegram configuration commands."""

    def __init__(self) -> None:
        self.pending_qr_messages: dict[int, discord.Message] = {}

    @app_commands.command(name="login", description="Faz login no Telegram via QR code")
    @app_commands.describe(
        senha="Senha 2FA (opcional, apenas se sua conta tiver autenticação de dois fatores)"
    )
    async def login(
        self, interaction: discord.Interaction, senha: str | None = None
    ) -> None:
        """Login to Telegram via QR code."""
        bot = get_bot()
        telegram_manager = get_client()

        # Check if user is bot owner
        if not is_owner(bot, interaction):
            await interaction.response.send_message(
                "Você não tem permissão para usar este comando.", ephemeral=True
            )
            return
        if not telegram_manager:
            await interaction.response.send_message(
                "Telegram client não está configurado.", ephemeral=True
            )
            return

        client = telegram_manager.client

        # Defer interaction immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)

        # Delete any previously pending QR code message for this user
        user_id = interaction.user.id
        if user_id in self.pending_qr_messages:
            old_qr_message = self.pending_qr_messages[user_id]
            try:
                await old_qr_message.delete()
            except Exception:
                pass  # Message might have already been deleted
            del self.pending_qr_messages[user_id]

        try:
            if not telegram_manager.is_connected():
                await telegram_manager.connect()

            if await telegram_manager.is_user_authorized():
                me = await telegram_manager.client.get_me()
                await interaction.followup.send(
                    f"Já está logado como **{me.first_name}** (@{me.username or 'sem username'})",
                    ephemeral=True,
                )
                return
        except AUTH_ERRORS:
            await interaction.followup.send(
                "**Erro de autenticação:** Por favor, tente fazer login novamente.",
                ephemeral=True,
            )
            return
        except Exception as e:
            await interaction.followup.send(
                f"**Erro ao conectar:** {str(e)}", ephemeral=True
            )
            return

        if senha:
            await interaction.followup.send(
                "Iniciando login via QR code... (senha 2FA fornecida)", ephemeral=True
            )
        else:
            await interaction.followup.send(
                "Iniciando login via QR code...", ephemeral=True
            )

        qr_message = None

        async def send_qr_url(
            url: str, expiration_seconds: int, expires_at: datetime.datetime
        ) -> None:
            nonlocal qr_message
            # Format expiration message
            expiration_msg = f"⏱️ Este QR code expira em **{expiration_seconds} segundos** (às {expires_at.strftime('%H:%M:%S')} UTC)"

            try:
                qr_image = telegram.gen_qr_image(url)
                file = discord.File(qr_image, filename="qrcode.png")
                qr_message = await interaction.followup.send(
                    f"Escaneie este QR code com o Telegram:\n{expiration_msg}",
                    file=file,
                    ephemeral=True,
                )
                self.pending_qr_messages[user_id] = qr_message
            except Exception:
                # Fallback to ASCII QR code if image generation fails
                ascii_qr = telegram.gen_qr_ascii(url)
                qr_message = await interaction.followup.send(
                    f"Escaneie este QR code com o Telegram:\n{expiration_msg}\n```\n{ascii_qr}\n```",
                    ephemeral=True,
                )
                self.pending_qr_messages[user_id] = qr_message

        async def cleanup_qr_message() -> None:
            nonlocal qr_message
            if qr_message:
                try:
                    await qr_message.delete()
                except Exception:
                    pass
            if user_id in self.pending_qr_messages:
                del self.pending_qr_messages[user_id]

        async def send_success() -> None:
            await cleanup_qr_message()
            me = await telegram_manager.client.get_me()
            await interaction.followup.send(
                f"Login realizado com sucesso! Logado como **{me.first_name}**",
                ephemeral=True,
            )

        async def on_qr_expired() -> None:
            await cleanup_qr_message()
            await interaction.followup.send(
                "**QR code expirado!** Por favor, use `/telegram login` novamente para gerar um novo QR code.",
                ephemeral=True,
            )

        async def get_password() -> str:
            if senha:
                return senha
            raise ValueError(
                "Senha 2FA necessária. Use `/telegram login senha:sua_senha` para fornecer a senha."
            )

        async def run_login() -> None:
            try:
                await telegram.login(
                    client,
                    qr_callback=send_qr_url,
                    success_callback=send_success,
                    expired_callback=on_qr_expired,
                    password_callback=get_password,
                )
            except AUTH_ERRORS:
                await interaction.followup.send(
                    "**Erro de autenticação:** Por favor, tente fazer login novamente.",
                    ephemeral=True,
                )
            except PASSWORD_ERRORS:
                await interaction.followup.send(
                    "**Senha inválida:** A senha fornecida está incorreta. Por favor, verifique e tente novamente.",
                    ephemeral=True,
                )
            except TIMEOUT_ERRORS:
                # Timeout/expired errors are handled by expired_callback
                pass
            except ValueError as e:
                # Password-related errors (e.g., password not provided)
                await interaction.followup.send(f"**Erro:** {str(e)}", ephemeral=True)
            except Exception as e:
                # Other unexpected errors
                await interaction.followup.send(
                    f"**Erro durante o login:** {str(e)}", ephemeral=True
                )
            finally:
                # Always cleanup QR message, even if success/expired callbacks already did it
                # cleanup_qr_message is idempotent, so calling it multiple times is safe
                await cleanup_qr_message()

        asyncio.create_task(run_login())


async def setup(bot: commands.Bot) -> None:
    """Setup function to add the cog to the bot."""
    await bot.add_cog(Telegram())
