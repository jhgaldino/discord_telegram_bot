import asyncio
import datetime
import io
import sys
from collections.abc import Awaitable, Callable
from contextlib import suppress

import qrcode
import telethon
from discord.utils import utcnow

from src.services.telegram.exceptions import AUTH_ERRORS, PASSWORD_ERRORS

# Type aliases for callback functions
QRCallback = Callable[[str, int, datetime.datetime], Awaitable[None]]
SuccessCallback = Callable[[], Awaitable[None]]
ExpiredCallback = Callable[[], Awaitable[None]]
PasswordCallback = Callable[[], Awaitable[str]]


def gen_qr_ascii(url: str) -> str:
    qr = qrcode.QRCode()
    qr.add_data(url)
    qr.make(fit=True)

    # Capture the ASCII output
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    try:
        qr.print_ascii(invert=True)
        ascii_qr = buffer.getvalue()
    finally:
        sys.stdout = old_stdout

    return ascii_qr


def gen_qr_image(url: str) -> io.BytesIO:
    qr = qrcode.QRCode()
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = io.BytesIO()
    img.save(img_buffer, format="PNG")
    img_buffer.seek(0)
    return img_buffer


async def login(
    client: telethon.TelegramClient,
    qr_callback: QRCallback,
    success_callback: SuccessCallback,
    expired_callback: ExpiredCallback,
    password_callback: PasswordCallback,
) -> bool:
    if not client.is_connected():
        try:
            await client.connect()
        except AUTH_ERRORS:
            with suppress(Exception):
                await client.disconnect()
        except (ConnectionError, TimeoutError):
            raise

    try:
        is_authorized = await client.is_user_authorized()
    except AUTH_ERRORS:
        is_authorized = False

    if is_authorized:
        await success_callback()
        return True

    # Note: Telegram QR login tokens typically expire after 30 seconds
    qr_login = await client.qr_login()

    expires_at = qr_login.expires
    now = utcnow()
    expiration_seconds = max(1, int((expires_at - now).total_seconds()))

    await qr_callback(qr_login.url, expiration_seconds, expires_at)

    try:
        timeout = expiration_seconds + 5  # Add 5 second buffer
        await asyncio.wait_for(
            qr_login.wait(expiration_seconds), timeout=float(timeout)
        )
    except AUTH_ERRORS + PASSWORD_ERRORS:
        raise
    except telethon.errors.rpcerrorlist.SessionPasswordNeededError:
        try:
            password = await password_callback()
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Error getting password: {str(e)}") from e

        if not password:
            raise ValueError(
                "Telegram Two-Factor Authentication password required."
            ) from None

        try:
            await client.sign_in(password=password)
        except PASSWORD_ERRORS:
            raise
    except (TimeoutError, asyncio.CancelledError) as e:
        # Check if user scanned QR during timeout
        if await client.is_user_authorized():
            return True

        with suppress(Exception):
            await expired_callback()

        if isinstance(e, asyncio.CancelledError):
            try:
                await client.is_user_authorized()
            except AUTH_ERRORS:
                raise

        raise

    if not await client.is_user_authorized():
        raise RuntimeError("Login failed. User not authorized after scanning QR code")

    await success_callback()
    return True
