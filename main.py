import os
import re
import discord
from discord.ext import commands
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from dotenv import load_dotenv

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
telegram_session_string = os.environ.get('TELEGRAM_SESSION_STRING')

# Valores do Discord
discord_token = os.environ.get('DISCORD_TOKEN')
discord_channel_ids = [int(str_id) for str_id in os.environ.get('DISCORD_CHANNEL_ID').split(',')]

# Variável global para armazenar o contexto
discord_channels = set()
# Inicializa a sessão do Telegram
client = TelegramClient(StringSession(telegram_session_string), api_id, api_hash)

def filter(event):
    if re.search(r'https://', event.raw_text):
        return True
    return False

def format(event: events.NewMessage.Event):
    text = re.sub(r"\n+", "\n", event.raw_text)
    return text

# Evento para quando o bot do Discord estiver pronto
# Cria um manipulador de eventos para cada canal
for telegram_channel in telegram_channels:
    @client.on(events.NewMessage(chats=telegram_channel, func=filter))
    async def my_event_handler(event):
        text = format(event)
        # Envia a nova mensagem para o canal do Discord
        for channel in discord_channels:
            await channel.send(text)

@bot.event
async def on_ready():
    await client.start()
    print('Bot is ready.')
    for channel_id in discord_channel_ids:
        discord_channels.add(bot.get_channel(channel_id))
    for channel in discord_channels:
        await channel.send('Bot is ready.')

bot.run(discord_token)
