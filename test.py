from telethon import TelegramClient, events
import os
import discord
from discord.ext import commands

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

@client.on(events.NewMessage(chats=telegram_channels))
async def my_event_handler(event):
    global global_ctx
    # Envia a nova mensagem para o canal do Discord
    if global_ctx:
        await global_ctx.send(event.raw_text)

# Comando para iniciar a verificação de novas mensagens
@bot.command()
async def start_checking_messages(ctx):
    global global_ctx
    global_ctx = ctx
    await client.start()

bot.run(discord_token)