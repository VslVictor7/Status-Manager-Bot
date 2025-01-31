import discord
import asyncio
import pytz
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DOMAIN = os.getenv('DOMAIN', "false")
DOMAIN_IP = os.getenv('DOMAIN_IP')
PORT = int(os.getenv('MINECRAFT_PORT'))

async def get_public_ipv4(session):
    async with session.get("https://api.ipify.org?format=json") as response:
        return (await response.json()).get("ip")

async def get_server_status(bot):
    try:
        status = await bot.server.async_status()

        names = [player.name for player in status.players.sample] if status.players.sample else []
        player_names_sorted = sorted(names)

        return True, status.players.online, status.version.name, player_names_sorted
    except:
        return False, 0, "Desconhecido", []

async def update_message_periodically(message, session, bot_name, bot, interval=0.1):

    async def get_current_status():
        current_ip = await get_public_ipv4(session)
        server_online, players_online, version, player_names = await get_server_status(bot)
        return current_ip, server_online, players_online, version, player_names

    async def update_discord_message(message, embed):
        try:
            sao_paulo_tz = pytz.timezone('America/Sao_Paulo')
            current_time = datetime.now(sao_paulo_tz)
            await message.edit(embed=embed, content="")
            print(f"[BOT] Mensagem do servidor atualizada as: {current_time}.")
        except discord.DiscordException as e:
            print(f"[ERROR] Falha ao atualizar mensagem: {e}")

    def has_status_changed(current, last):
        if current["ip"] != last["ip"]:
            return True
        if current["server_online"] != last["server_online"]:
            return True
        if set(current["player_names"]) != set(last["player_names"]):
            return True
        if current["players_online"] != last["players_online"]:
            return True

        return False

    last_status = {
        "ip": None,
        "server_online": None,
        "players_online": None,
        "version": None,
        "player_names": None,
    }

    while True:
        try:
            current_ip, server_online, players_online, version, player_names = await get_current_status()

            if has_status_changed(
                {"ip": current_ip, "server_online": server_online, "players_online": players_online, "version": version, "player_names": player_names},
                last_status
            ):
                if "Anonymous Player" not in (player_names or []):

                    embed = create_embed(current_ip, server_online, players_online, version, player_names, bot_name)
                    await update_discord_message(message, embed)

                    last_status.update({
                        "ip": current_ip,
                        "server_online": server_online,
                        "players_online": players_online,
                        "version": version,
                        "player_names": player_names,
                    })

            await asyncio.sleep(interval)
        except Exception as e:
            print(f"[ERROR] Ocorreu um erro inesperado ao atualizar a mensagem do servidor: {e}")
            await asyncio.sleep(interval)
        except discord.DiscordException as e:
            print(f"[ERROR] Falha ao atualizar mensagem: {e}")
            await asyncio.sleep(interval)

def create_embed(ip, server_online, players_online, version, player_names, bot_name):
    sao_paulo_tz = pytz.timezone('America/Sao_Paulo')
    current_time = datetime.now(sao_paulo_tz)

    embed = discord.Embed(
        title="Status do Servidor Minecraft",
        color=0x00ff00 if server_online else 0xff0000
    )

    if DOMAIN == "true":
        embed.add_field(name="🖥️ IP", value=f"{DOMAIN_IP}" if server_online else "Nenhum", inline=False)
    else:
        embed.add_field(name="🖥️ IP", value=f"{ip}:{PORT}" if server_online else "Nenhum", inline=False)

    embed.add_field(name="📶 Status", value="🟢 Online" if server_online else "🔴 Offline", inline=False)
    embed.add_field(
        name="👥 Jogadores Online",
        value="Nenhum" if players_online == 0 else f"{players_online} jogador{'es' if players_online != 1 else ''}",
        inline=False
    )

    embed.add_field(name="📝 Nomes", value=", ".join(player_names) if player_names else "Nenhum", inline=False)

    embed.add_field(name="🌐 Versão", value=version, inline=False)

    embed.timestamp = current_time

    embed.set_footer(
        text=bot_name
    )

    return embed