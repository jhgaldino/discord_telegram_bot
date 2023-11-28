import os
import re
import discord
from discord.ext import commands
from telethon import TelegramClient, events

# Inicializa os intents do Discord
intents = discord.Intents.default()
intents.message_content = True

# Inicializa o bot do Discord com os intents
bot = commands.Bot(command_prefix='!', intents=intents)

# Valores do Telegram
api_id = os.environ.get('TELEGRAM_API_ID')
api_hash = os.environ.get('TELEGRAM_API_HASH')
client = TelegramClient('anon', api_id, api_hash)

discord_token = os.environ.get('DISCORD_TOKEN')
telegram_channels = os.environ.get('TELEGRAM_CHANNELS').split(',')

# Variável global para armazenar o contexto
global_ctx = None

def filter(event):
    if re.search(r'https://', event.raw_text):
        return True
    return False

def format(event: events.NewMessage.Event):
    text = re.sub(r"\n+", "\n", event.raw_text)
    return text

# Exemplo de Teste de eventos
# @client.on(events.NewMessage(func=filter))
# async def teste(event):
#     text = format(event)
#     print(text)

# Evento para quando o bot do Discord estiver pronto
@client.on(events.NewMessage(chats=telegram_channels, func=filter))
async def my_event_handler(event):
    # Envia a nova mensagem para o canal do Discord
    if global_ctx:
        text = format(event)
        await global_ctx.send(text) 

# Comando para iniciar a verificação de novas mensagens
@bot.command(name='start')
async def start_checking_messages(ctx):
    global global_ctx
    global_ctx = ctx
    await client.start()

bot.run(discord_token)
