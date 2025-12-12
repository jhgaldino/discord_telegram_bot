import asyncio
import os
import re
import discord
from discord import app_commands

from discord.ext import commands
from telethon import TelegramClient, events
from dotenv import load_dotenv

import src.reminders as reminders
import src.telegram as telegram
from src.error import AUTH_ERRORS, PASSWORD_ERRORS, TIMEOUT_ERRORS
from src.utils import plural, format_list_to_markdown, string_to_list

load_dotenv()

# Inicializa os intents do Discord
intents = discord.Intents.default()
intents.message_content = True
command_prefix = '🝍' # Não usamos comandos por prefixo, mas precisamos de um valor para inicializar o bot

# Inicializa o bot do Discord com os intents
bot = commands.Bot(command_prefix=command_prefix, intents=intents)

# Valores do Telegram
api_id = os.environ.get('TELEGRAM_API_ID')
api_hash = os.environ.get('TELEGRAM_API_HASH')
telegram_channels = string_to_list(os.environ.get('TELEGRAM_CHANNELS'))

# Valores do Discord
discord_token = os.environ.get('DISCORD_TOKEN')
discord_channel_ids = [int(ch) for ch in string_to_list(os.environ.get('DISCORD_CHANNEL_IDS'))]

# Variável global para armazenar o contexto
discord_channels = set()

# Track pending QR code messages per user
pending_qr_messages = {}

# Inicializa a sessão do Telegram
client = TelegramClient("telegram", api_id, api_hash)

def filter(event):
    if re.search(r'https://', event.raw_text):
        return True
    return False

def format(event: events.NewMessage.Event):
    text = re.sub(r"\n+", "\n", event.raw_text)
    return text

async def send_dm_to_user(message: str, user_id: int):
    user = await bot.fetch_user(user_id)
    await user.send(message)

# Evento para quando o bot do Discord estiver pronto
# Cria um manipulador de eventos para cada canal
for telegram_channel in telegram_channels:
    @client.on(events.NewMessage(chats=telegram_channel, func=filter))
    async def my_event_handler(event):
        text_to_channel = format(event)
        
        # Coleta todas as tarefas para execução paralela
        tasks = []
        
        # Envia a nova mensagem para cada canal do Discord
        for channel in discord_channels:
            tasks.append(channel.send(text_to_channel))

        # Envia uma mensagem para cada usuario que está marcado para o texto
        reminder_by_user = reminders.find_by_user_in_text(text_to_channel)                
        for user_id, reminder_list in reminder_by_user.items():
            markdown_list = format_list_to_markdown(reminder_list)
            text_to_user = text_to_channel + f'\n\nVocê me pediu para te lembrar de:\n{markdown_list}'
            tasks.append(send_dm_to_user(text_to_user, user_id))

        # Executa todas as tarefas em paralelo
        await asyncio.gather(*tasks)

@bot.event
async def on_ready():
    startup_tasks = [
        client.connect(),
        bot.tree.sync(),
    ]
    await asyncio.gather(*startup_tasks)
    
    print('Bot is ready.')

    for channel_id in discord_channel_ids:
        discord_channels.add(bot.get_channel(channel_id))
    for channel in discord_channels:
        await channel.send('Bot is ready.')

@bot.tree.command(name='lembrar', description='Peça para o bot te lembrar quando encontrar um texto específico')
async def setup_reminder(interaction: discord.Interaction, lembrete: str):    
    reminders.add_user_to_reminder(interaction.user.id, lembrete) 
    await interaction.response.send_message(f'Vou te lembrar quando encontrar **{lembrete}**')

@bot.tree.command(name='listar', description='Mostra os lembretes que o bot está guardando pra você')
async def list_reminders(interaction: discord.Interaction):
    reminder_list = reminders.list_by_user(interaction.user.id)    
    if not reminder_list:
        await interaction.response.send_message('Você não tem nenhum lembrete guardado')
        return

    markdown_list = format_list_to_markdown(reminder_list)
    quant = len(reminder_list)
    message = f'Você tem {quant} lembrete{plural(quant, "", "s")} guardado{plural(quant, "", "s")}:\n{markdown_list}'
    await interaction.response.send_message(message)

@bot.tree.command(name='esquecer', description='Remove um lembrete da lista')
async def forget_reminder(interaction: discord.Interaction, lembrete: str):
    reminders.remove_user_from_reminder(interaction.user.id, lembrete)
    await interaction.response.send_message(f'Não vou mais te lembrar de **{lembrete}**')

@bot.tree.command(name='status', description='Mostra vários status do bot')
async def status(interaction: discord.Interaction):
    # Check if user is bot owner
    if not is_owner(interaction):
        await interaction.response.send_message('Você não tem permissão para usar este comando.', ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    
    status_lines = []
    
    # Discord bot status
    status_lines.append(f"📊 **Latência:** {round(bot.latency * 1000)}ms")
    status_lines.append(f"✅ **Discord Bot:** Online")

    # Telegram connection status
    try:
        is_connected = client.is_connected()
        if is_connected:
            status_lines.append("✅ **Telegram:** Conectado")
            
            # Check authentication
            try:
                is_authorized = await client.is_user_authorized()
                if is_authorized:
                    me = await client.get_me()
                    status_lines.append(f"✅ **Autenticação:** Logado como **{me.first_name}** (@{me.username or 'sem username'})")
                else:
                    status_lines.append("❌ **Autenticação:** Não autenticado (use `/login`)")
            except AUTH_ERRORS as e:
                status_lines.append(f"❌ **Autenticação:** Erro - {str(e)}")
            except Exception as e:
                status_lines.append(f"⚠️ **Autenticação:** Erro ao verificar - {str(e)}")
        else:
            status_lines.append("❌ **Telegram:** Desconectado")
    except Exception as e:
        status_lines.append(f"❌ **Telegram:** Erro ao verificar conexão - {str(e)}")
    
    message = "\n".join(status_lines)
    await interaction.followup.send(message, ephemeral=True)

def is_owner(interaction: discord.Interaction) -> bool:
    if bot.owner_id:
        return interaction.user.id == bot.owner_id
    # Fallback: check application owners
    app = interaction.client.application
    if app and app.owner:
        if isinstance(app.owner, discord.Team):
            return interaction.user.id in [member.id for member in app.owner.members]
        return interaction.user.id == app.owner.id
    return False

@bot.tree.command(name='login', description='Faz login no Telegram via QR code')
@app_commands.describe(senha='Senha 2FA (opcional, apenas se sua conta tiver autenticação de dois fatores)')
async def telegram_login(interaction: discord.Interaction, senha: str = None):
    # Check if user is bot owner
    if not is_owner(interaction):
        await interaction.response.send_message('Você não tem permissão para usar este comando.', ephemeral=True)
        return
    
    # Defer interaction immediately to prevent timeout
    await interaction.response.defer(ephemeral=True)
    
    # Delete any previously pending QR code message for this user
    user_id = interaction.user.id
    if user_id in pending_qr_messages:
        old_qr_message = pending_qr_messages[user_id]
        try:
            await old_qr_message.delete()
        except Exception:
            pass  # Message might have already been deleted
        del pending_qr_messages[user_id]
    
    try:
        if not client.is_connected():
            await client.connect()
        
        if await client.is_user_authorized():
            me = await client.get_me()
            await interaction.followup.send(f'Já está logado como **{me.first_name}** (@{me.username or "sem username"})', ephemeral=True)
            return
    except AUTH_ERRORS as e:
        await interaction.followup.send(f'**Erro de autenticação:** Por favor, tente fazer login novamente.', ephemeral=True)
        return
    except Exception as e:
        await interaction.followup.send(f'**Erro ao conectar:** {str(e)}', ephemeral=True)
        return
    
    if senha:
        await interaction.followup.send('Iniciando login via QR code... (senha 2FA fornecida)', ephemeral=True)
    else:
        await interaction.followup.send('Iniciando login via QR code...', ephemeral=True)
    
    qr_message = None
    
    async def send_qr_url(url: str):
        nonlocal qr_message
        try:
            qr_image = telegram.gen_qr_image(url)
            file = discord.File(qr_image, filename='qrcode.png')
            qr_message = await interaction.followup.send('Escaneie este QR code com o Telegram:', file=file, ephemeral=True)
            pending_qr_messages[user_id] = qr_message
        except Exception:
            # Fallback to ASCII QR code if image generation fails
            ascii_qr = telegram.gen_qr_ascii(url)
            qr_message = await interaction.followup.send(f'Escaneie este QR code com o Telegram:\n```\n{ascii_qr}\n```', ephemeral=True)
            pending_qr_messages[user_id] = qr_message
    
    async def cleanup_qr_message():
        nonlocal qr_message
        if qr_message:
            try:
                await qr_message.delete()
            except Exception:
                pass
        if user_id in pending_qr_messages:
            del pending_qr_messages[user_id]
    
    async def send_success():
        await cleanup_qr_message()
        me = await client.get_me()
        await interaction.followup.send(f'Login realizado com sucesso! Logado como **{me.first_name}**', ephemeral=True)
    
    async def on_qr_expired():
        await cleanup_qr_message()
        await interaction.followup.send('**QR code expirado!** Por favor, use `/login` novamente para gerar um novo QR code.', ephemeral=True)
    
    async def get_password():
        if senha:
            return senha
        raise ValueError("Senha 2FA necessária. Use `/login senha:sua_senha` para fornecer a senha.")
    
    async def run_login():
        try:
            await telegram.login(client, qr_callback=send_qr_url, success_callback=send_success, expired_callback=on_qr_expired, password_callback=get_password)
        except AUTH_ERRORS:
            await interaction.followup.send('**Erro de autenticação:** Por favor, tente fazer login novamente.', ephemeral=True)
        except PASSWORD_ERRORS:
            await interaction.followup.send('**Senha inválida:** A senha fornecida está incorreta. Por favor, verifique e tente novamente.', ephemeral=True)
        except TIMEOUT_ERRORS:
            # Timeout/expired errors are handled by expired_callback
            pass
        except ValueError as e:
            # Password-related errors (e.g., password not provided)
            await interaction.followup.send(f'**Erro:** {str(e)}', ephemeral=True)
        except Exception as e:
            # Other unexpected errors
            await interaction.followup.send(f'**Erro durante o login:** {str(e)}', ephemeral=True)
        finally:
            # Always cleanup QR message, even if success/expired callbacks already did it
            # cleanup_qr_message is idempotent, so calling it multiple times is safe
            await cleanup_qr_message()
    
    asyncio.create_task(run_login())

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message('Você não tem permissão para usar este comando.', ephemeral=True)
    else:
        await interaction.response.send_message(f'Ocorreu um erro: {str(error)}', ephemeral=True)
        raise error

bot.run(discord_token)
