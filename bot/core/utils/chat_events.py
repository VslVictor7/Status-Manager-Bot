import os
import pytz
from datetime import datetime
from dotenv import load_dotenv
from mcrcon import MCRcon

load_dotenv()

RCON_HOST = os.getenv("RCON_HOST")
RCON_PORT = int(os.getenv("RCON_PORT"))
RCON_PASSWORD = os.getenv("RCON_PASSWORD")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_CHAT_EVENTS_ID"))


async def message_on_server(bot):

    @bot.event
    async def on_message(message):
        if message.author.bot:
            return

        if message.channel.id != DISCORD_CHANNEL_ID:
            return

        display_name = message.author.display_name
        content = message.content

        minecraft_message = f"{display_name} >> {content}"

        sao_paulo_tz = pytz.timezone('America/Sao_Paulo')
        current_time = datetime.now(sao_paulo_tz)

        try:
            with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
                mcr.command(f"say {minecraft_message}")
            print(f"[BOT TEXT SENT] {minecraft_message} | {current_time}")
        except Exception as e:
            print(f"[BOT ERROR] Falha ao enviar mensagem para o servidor Minecraft: {e}")