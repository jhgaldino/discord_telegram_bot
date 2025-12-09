import io
import sys
import asyncio
import telethon
import qrcode
from src.error import AUTH_ERRORS, PASSWORD_ERRORS

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
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    return img_buffer

async def login(client: telethon.TelegramClient, qr_callback=None, success_callback=None, expired_callback=None, password_callback=None):
    # Connect if not connected, handle auth errors gracefully
    if not client.is_connected():
        try:
            await client.connect()
        except AUTH_ERRORS:
            # Disconnect cleanly on auth errors, will trigger login flow
            try:
                await client.disconnect()
            except Exception:
                pass
        except Exception:
            raise
    
    # Check authorization, treat auth errors as not authorized
    try:
        is_authorized = await client.is_user_authorized()
    except AUTH_ERRORS:
        is_authorized = False
    
    if is_authorized:
        if success_callback:
            await success_callback()
        return True
    
    # Start QR login flow
    qr_login = await client.qr_login()
    if qr_callback:
        await qr_callback(qr_login.url)
    
    try:
        await asyncio.wait_for(qr_login.wait(60), timeout=60.0)
    except (AUTH_ERRORS, PASSWORD_ERRORS):
        raise
    except telethon.errors.rpcerrorlist.SessionPasswordNeededError:
        # Handle 2FA password requirement
        if not password_callback:
            raise ValueError("Senha 2FA necessária. Por favor, forneça uma senha.")
        
        try:
            password = await password_callback()
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Erro ao obter senha: {str(e)}")
        
        if not password:
            raise ValueError("Senha 2FA necessária")
        
        try:
            await client.sign_in(password=password)
        except PASSWORD_ERRORS:
            raise
    except (asyncio.TimeoutError, asyncio.CancelledError) as e:
        # Check if user scanned QR during timeout
        if await client.is_user_authorized():
            return True
        
        if expired_callback:
            try:
                await expired_callback()
            except Exception:
                pass
        
        # Check if cancellation was due to auth error
        if isinstance(e, asyncio.CancelledError):
            try:
                await client.is_user_authorized()
            except AUTH_ERRORS:
                raise
        
        raise
    
    # Verify login succeeded
    if not await client.is_user_authorized():
        raise RuntimeError("Falha no login - usuário não autorizado após escanear QR code")
    
    if success_callback:
        await success_callback()
    return True
