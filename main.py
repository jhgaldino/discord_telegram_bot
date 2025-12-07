import asyncio
import os
import re
import discord

from discord.ext import commands
from telethon import TelegramClient, events
from dotenv import load_dotenv

import src.reminders as reminders
from src.utils import plural, format_list_to_markdown

load_dotenv()

# Inicializa os intents do Discord
intents = discord.Intents.default()
intents.message_content = True

# Inicializa o bot do Discord com os intents
bot = commands.Bot(command_prefix='!', intents=intents)

# Valores do Telegram
api_id = os.environ.get('TELEGRAM_API_ID')
api_hash = os.environ.get('TELEGRAM_API_HASH')
telegram_channels = os.environ.get('TELEGRAM_CHANNELS').split(',')
telegram_session_name = os.environ.get('TELEGRAM_SESSION_NAME')

# Valores do Discord
discord_token = os.environ.get('DISCORD_TOKEN')
discord_channel_ids = [int(str_id) for str_id in os.environ.get('DISCORD_CHANNEL_IDS').split(',')]

# Variável global para armazenar o contexto
discord_channels = set()
# Inicializa a sessão do Telegram
client = TelegramClient(telegram_session_name, api_id, api_hash)

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
    # Inicia o cliente do Telegram e sincroniza o tree do bot em paralelo
    tasks = [
        client.start(),
        bot.tree.sync(),
    ]
    await asyncio.gather(*tasks)

    print('Bot is ready.')

    for channel_id in discord_channel_ids:
        discord_channels.add(bot.get_channel(channel_id))
    for channel in discord_channels:
        await channel.send('Bot is ready.')

@bot.hybrid_command(name='lembrar', description='Peça para o bot te lembrar quando encontrar um texto específico')
async def setup_reminder(ctx: commands.Context, lembrete: str):    
    reminders.add_user_to_reminder(ctx.author.id, lembrete) 
    await ctx.send(f'Vou te lembrar quando encontrar **{lembrete}**')

@bot.hybrid_command(name='listar', description='Mostra os lembretes que o bot está guardando pra você')
async def list_reminders(ctx: commands.Context):
    reminder_list = reminders.list_by_user(ctx.author.id)    
    if not reminder_list:
        await ctx.send('Você não tem nenhum lembrete guardado')
        return

    markdown_list = format_list_to_markdown(reminder_list)
    quant = len(reminder_list)
    message = f'Você tem {quant} lembrete{plural(quant, "", "s")} guardado{plural(quant, "", "s")}:\n{markdown_list}'
    await ctx.send(message)

@bot.hybrid_command(name='esquecer', description='Remove um lembrete da lista')
async def forget_reminder(ctx: commands.Context, lembrete: str):
    reminders.remove_user_from_reminder(ctx.author.id, lembrete)
    await ctx.send(f'Não vou mais te lembrar de **{lembrete}**')

bot.run(discord_token)
