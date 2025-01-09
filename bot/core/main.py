import discord
import os
import aiohttp
import asyncio
from scripts.mybot import MyBot
from scripts.message_manager import update_message_periodically
from logs.monitoring.server_log import monitor_file
from utils.chat_events import message_on_server
from utils import ranking_players
from logs.log_handler import log_handling
from scripts.player_events import start_player_events
from commands import setup_commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
MESSAGE_ID = int(os.getenv('MESSAGE_ID'))

bot = MyBot()

@bot.event
async def on_ready():

    print(f"[BOT] Logado como {bot.user.name} - {bot.user.id}")

    activity = discord.Activity(type=discord.ActivityType.watching, name="Movimentação do nosso servidor")
    await bot.change_presence(status=discord.Status.online, activity=activity)

    interval = 60
    print(f"[BOT] Esperando {interval} segundos antes de iniciar as tarefas...")
    await asyncio.sleep(interval)

    bot.loop.create_task(ranking_players.raking_players())

    await background_tasks()

    async with aiohttp.ClientSession() as session:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            try:
                message = await channel.fetch_message(MESSAGE_ID)
                print("[BOT STARTED] Pronto para monitoramento de IP, Servidor, Jogadores.")

                await update_message_periodically(message, session)

            except discord.DiscordException as e:
                print(f"[BOT ERROR] Erro ao buscar mensagem: {e}")
                await bot.close()
        else:
            print("[BOT ERROR] Canal não detectado.")
            await bot.close()


async def background_tasks():
    try:
        await bot.wait_until_ready()

        bot.loop.create_task(message_on_server(bot))
        bot.loop.create_task(setup_commands(bot))
        bot.loop.create_task(bot.sync_commands())
        bot.loop.create_task(bot.uptime_start_count())
        bot.loop.create_task(start_player_events(bot))
        bot.loop.create_task(log_handling(bot))

        #bot.loop.create_task(monitor_file(bot))

    except Exception as e:
        print(f"[BOT ERROR] Erro ao iniciar tarefas em segundo plano: {e}")
        await bot.close()


if __name__ == '__main__':
    bot.run(TOKEN)