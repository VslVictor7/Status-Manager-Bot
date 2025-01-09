import re
import discord
import os
from logs.api_call import fetch_data_from_api
from .offline_player_loader import load_json
from dotenv import load_dotenv

load_dotenv()

API_PORT = int(os.getenv("API_PORT"))
SERVER_MODE = os.getenv("SERVER_MODE", "0")

offline_players = load_json("players.json")
default_uuid = "c2e45a26339547ff86c0b3dd0c2aa2d2"

async def process_death_event(log_line, channel):
    try:
        ignore_patterns = [
            "[Rcon]", "[Not Secure]", "Disconnecting VANILLA connection attempt",
            "rejected vanilla connections", "lost connection", "id=<null>", "legacy=false",
            "lost connection: Disconnected", "<init>", "<", ">", "x=", "y=", "z="
        ]

        if any(pattern in log_line for pattern in ignore_patterns):
            return

        death_messages = await fetch_data_from_api(f"http://endpoint:{API_PORT}/deaths")
        mobs = await fetch_data_from_api(f"http://endpoint:{API_PORT}/mobs")

        for death_pattern, translated_message in death_messages.items():
            search_pattern = death_pattern.replace("{player}", r"(?P<player>\S+)")

            if "{entity}" in search_pattern:
                search_pattern = search_pattern.replace("{entity}", r"(?P<entity>[\w\s]+)")
            if "{item}" in search_pattern:
                search_pattern = search_pattern.replace("{item}", r"(?P<item>[\w\s]+)")

            match = re.search(search_pattern, log_line)
            if match:
                player = match.group("player")
                raw_entity = match.groupdict().get("entity") or "desconhecido"
                raw_item = match.groupdict().get("item") or "desconhecido"

                entity = mobs.get(raw_entity.strip(), raw_entity)
                item = mobs.get(raw_item.strip(), raw_item)

                translated = translated_message
                translated = translated.replace("{entity}", entity)
                translated = translated.replace("{item}", item)

                await send_player_event(channel, player, translated, 0x000000)
                return
    except Exception as e:
        print(f"[BOT ERROR] Erro ao processar evento de morte: {e}")

async def send_player_event(channel, player_name, event_message, color):
    try:
        uuid = player_name
        if SERVER_MODE != "0":
            for username, player_data in offline_players.items():
                if player_name == username and player_data["original"] == False:
                    uuid = default_uuid
        embed = discord.Embed(color=color)
        embed.set_author(
            name=f"{player_name} {event_message}".strip("'\""),
            icon_url=f"https://mineskin.eu/helm/{uuid}"
        )
        await channel.send(embed=embed)
    except Exception as e:
        print(f"[BOT ERROR] Erro ao enviar evento de morte: {e}")
