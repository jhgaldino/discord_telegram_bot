import asyncio
import datetime
from contextlib import suppress

import discord
from discord import app_commands
from discord.ext import commands

from src.services.telegram import qr as telegram
from src.services.telegram.exceptions import AUTH_ERRORS, PASSWORD_ERRORS
from src.shared.permissions import admin_only
from src.shared.services import services


class Telegram(
    commands.GroupCog,
    name="telegram",
    description="Comandos de configuração do Telegram",
):
    def __init__(self) -> None:
        self.pending_qr_messages: dict[int, discord.Message] = {}

    @app_commands.command(name="login", description="Faz login no Telegram via QR code")
    @app_commands.describe(
        senha="Senha 2FA (opcional, apenas se sua conta tiver autenticação de dois fatores)"
    )
    @admin_only()
    async def login(
        self, interaction: discord.Interaction, senha: str | None = None
    ) -> None:
        # Defer interaction immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)

        # Delete any previously pending QR code message for this user
        user_id = interaction.user.id
        if user_id in self.pending_qr_messages:
            old_qr_message = self.pending_qr_messages[user_id]
            with suppress(discord.NotFound, discord.HTTPException):
                await old_qr_message.delete()
            del self.pending_qr_messages[user_id]

        try:
            if not services.client.is_connected():
                await services.client.connect()

            me = await services.client.get_me()
            if me:
                await interaction.followup.send(
                    f"Já está logado como **{me.first_name}** (@{me.username})",
                    ephemeral=True,
                )
                return
        except AUTH_ERRORS:
            await interaction.followup.send(
                "**Erro de autenticação:** Por favor, tente fazer login novamente.",
                ephemeral=True,
            )
            return
        except (ConnectionError, TimeoutError) as e:
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
            except (ValueError, OSError):
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
                with suppress(discord.NotFound, discord.HTTPException):
                    await qr_message.delete()
            if user_id in self.pending_qr_messages:
                del self.pending_qr_messages[user_id]

        async def send_success() -> None:
            await cleanup_qr_message()
            me = await services.client.get_me()
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
            raise ValueError("Telegram Two-Factor Authentication password required.")

        async def run_login() -> None:
            try:
                await telegram.login(
                    services.client,
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
            except (TimeoutError, asyncio.CancelledError):
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
    await bot.add_cog(Telegram())
