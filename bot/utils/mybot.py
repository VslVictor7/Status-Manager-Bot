import discord
import os
import pytz
from discord.ext import commands
from dotenv import load_dotenv
from mcstatus import JavaServer
from datetime import datetime

load_dotenv()

MINECRAFT_SERVER_IP = os.getenv('MINECRAFT_SERVER_IP')
MINECRAFT_SERVER_PORT = os.getenv('MINECRAFT_SERVER_PORT')

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
        self.uptime_start = None
        self.server = JavaServer.lookup(f"{MINECRAFT_SERVER_IP}:{MINECRAFT_SERVER_PORT}")

    async def setup_hook(self):
        await self.tree.sync()

    async def get_server_uptime(self):
        try:
            status = self.server.status()
            if status:
                if self.uptime_start is None:
                    sao_paulo_tz = pytz.timezone('America/Sao_Paulo')
                    self.uptime_start = datetime.now(sao_paulo_tz)
                return True, self.uptime_start
            else:
                return False, 0
        except Exception as e:
            print(f"Erro ao tentar acessar o servidor: {e}")
            return False, 0