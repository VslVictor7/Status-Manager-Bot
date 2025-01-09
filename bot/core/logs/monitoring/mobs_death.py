import re
import os
import discord
import aiohttp
from logs.api_call import fetch_data_from_api
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_PORT = int(os.getenv("API_PORT"))

async def process_mobs_death_event(line, channel):
    try:

        ignore_patterns = [
            "[Rcon]", "[Not Secure]", "Disconnecting VANILLA connection attempt",
            "rejected vanilla connections", "lost connection", "id=<null>", "legacy=false",
            "lost connection: Disconnected", "<init>", "<", ">"
        ]


        if any(pattern in line for pattern in ignore_patterns):
            return

        pattern = r"Named entity '?(?P<mob>[A-Za-z]+)'?|\bVillager\b"
        match_mob = re.search(pattern, line)

        if match_mob:
            captured_value = match_mob.group("mob") or "Villager"

            death_messages, mobs = await api_fetching()

            for death_pattern, translated_message in death_messages.items():
                search_pattern = death_pattern.replace("{player}", r"(?P<player>[\w\s]+(?:\d+)?)")

                if "{entity}" in search_pattern:
                    search_pattern = search_pattern.replace("{entity}", r"(?P<entity>[\w\s]+)")
                if "{item}" in search_pattern:
                    search_pattern = search_pattern.replace("{item}", r"(?P<item>[\w\s]+)")

                match = re.search(search_pattern, line)
                if match:
                    placeholder = match.group("player")

                    temp_dir = Path("temp_cache")
                    temp_dir.mkdir(exist_ok=True)
                    sanitized_value = captured_value.replace("Entity", "").strip()
                    icon_path = temp_dir / f"{sanitized_value}.png"

                    icon_url = await api_icon_fetching(sanitized_value)

                    await download_image(icon_url, icon_path)

                    raw_entity = match.groupdict().get("entity") or "desconhecido"
                    raw_item = match.groupdict().get("item") or "desconhecido"

                    named = mobs.get(placeholder.strip(), placeholder)
                    entity = mobs.get(raw_entity.strip(), raw_entity)
                    item = mobs.get(raw_item.strip(), raw_item)

                    translated = translated_message
                    translated = translated.replace("{entity}", entity)
                    translated = translated.replace("{item}", item)

                    await send_player_event(channel, named, translated, 0x000000, icon_path)
                    os.remove(icon_path)
                    return
    except Exception as e:
        print(f"[BOT ERROR] Erro ao processar evento de morte: {e}")

async def send_player_event(channel, name, event_message, color, icon_path):
    try:
        file = discord.File(icon_path, filename=os.path.basename(icon_path))
        embed = discord.Embed(color=color)
        embed.set_author(
            name=f"{name} {event_message}".strip("'\""),
            icon_url=f"attachment://{os.path.basename(icon_path)}"
        )
        await channel.send(file=file,embed=embed)
    except Exception as e:
        print(f"[BOT ERROR] Erro ao enviar evento de morte: {e}")

async def download_image(url, save_path):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    with open(save_path, "wb") as f:
                        f.write(image_data)
                    return True
                else:
                    return False
    except Exception as e:
        print(f"[BOT ERROR] Erro ao baixar a imagem: {e}")
        return False

async def api_fetching():
    try:
        death_messages = await fetch_data_from_api(f"http://endpoint:{API_PORT}/deaths")
        mobs_list = await fetch_data_from_api(f"http://endpoint:{API_PORT}/mobs")
        return death_messages, mobs_list
    except Exception as e:
        print(f"[BOT ERROR] Erro ao fazer requisição para a API: {e}")
        return

async def api_icon_fetching(mob):
    try:
        mob_data = await fetch_data_from_api(f'http://endpoint:{API_PORT}/images/{mob}')
        icon_url = mob_data.get('url')
        return icon_url
    except Exception as e:
        print(f"[BOT ERROR] Erro ao fazer requisição para a API: {e}")
        return "desconhecido"