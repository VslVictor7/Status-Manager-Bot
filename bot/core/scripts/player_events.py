import asyncio
import discord
import json
import os
from dotenv import load_dotenv
from mcrcon import MCRcon

load_dotenv()

DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_CHAT_EVENTS_ID"))
RCON_HOST = os.getenv("RCON_HOST")
RCON_PASSWORD = os.getenv("RCON_PASSWORD")
RCON_PORT = int(os.getenv("RCON_PORT"))
SERVER_MODE = os.getenv("SERVER_MODE", "0")

previous_players = set()
default_uuid = "c2e45a26339547ff86c0b3dd0c2aa2d2"

async def start_player_events(bot):
        await bot.wait_until_ready()
        channel = bot.get_channel(DISCORD_CHANNEL_ID)

        if not channel:
            print("[BOT ERROR] Canal do Discord não encontrado.")
            return

        print("[BOT INFO] Iniciando monitoramento do servidor Minecraft...")

        asyncio.create_task(check_player_events(channel))

async def check_player_events(channel):
    global previous_players
    while True:
        try:
            with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
                while True:
                    response = mcr.command("list")
                    players = extract_player_list(response)

                    joined = players - previous_players
                    for player in joined:
                        await send_player_event(channel, player, "entrou no servidor", 0x00FF00)

                    left = previous_players - players
                    for player in left:
                        await send_player_event(channel, player, "saiu do servidor", 0xFF0000)

                    previous_players = players
                    await asyncio.sleep(1)
        except Exception as e:
            print(f"[BOT ERROR] Erro ao verificar eventos de jogadores: {e}")
            interval = 60
            print(f"[BOT INFO] Tentando reconectar ao servidor com RCON em {interval} segundos...")
            await asyncio.sleep(60)

async def send_player_event(channel, player_name, event_message, color):
    uuid = player_name
    if SERVER_MODE != "0":
        for username, player_data in offline_players.items():
            if player_name == username and player_data["original"] == False:
                uuid = default_uuid
    embed = discord.Embed(color=color)
    embed.set_author(
        name=f"{player_name} {event_message}",
        icon_url=f"https://mineskin.eu/helm/{uuid}"
    )
    await channel.send(embed=embed)

def extract_player_list(response):
        try:
            if ":" in response:
                players_part = response.split(":")[1].strip()
                if players_part:
                    return set(players_part.split(", "))
            return set()
        except Exception:
            return set()

def load_json(file_name):
    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        file_path = os.path.join(base_dir, 'core', 'utils', 'json', file_name)

        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError as e:
        print(f"[BOT ERROR] Arquivo não encontrado: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"[BOT ERROR] Erro ao decodificar o arquivo: {e}")
        return {}

offline_players = load_json("players.json")