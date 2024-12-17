import discord, asyncio, pytz
from utils import database
from .mybot import MyBot
from datetime import datetime

bot = MyBot()

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


def create_embed(ip, server_online, players_online, version, player_names):
    sao_paulo_tz = pytz.timezone('America/Sao_Paulo')
    current_time = datetime.now(sao_paulo_tz)

    embed = discord.Embed(
        title="Status do Servidor Minecraft",
        color=0x00ff00 if server_online else 0xff0000
    )
    embed.add_field(name="🖥️ IP", value=f"{ip}:25565" if server_online else "Nenhum", inline=False)
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
        text="CraftMonitor"
    )

    return embed

async def update_message_periodically(channel, message, session, interval=3):

    async def get_current_status():
        current_ip = await get_public_ipv4(session)
        server_online, players_online, version, player_names = await get_server_status(bot)
        return current_ip, server_online, players_online, version, player_names

    def get_left_players(current_players, previous_players):
        return set(previous_players or []) - set(current_players or [])

    def update_database(player_name, server_online, players_online, left_players=None):
        if left_players:
            for player in left_players:
                database.insert_server_data(player_name, server_online, players_online, player_left=player)
        else:
            database.insert_server_data(player_name, server_online, players_online)

    async def update_discord_message(message, embed):
        try:
            sao_paulo_tz = pytz.timezone('America/Sao_Paulo')
            current_time = datetime.now(sao_paulo_tz)
            await message.edit(embed=embed, content="")
            print(f"[BOT] Mensagem do servidor atualizada as: {current_time}.")
        except discord.DiscordException as e:
            print(f"[ERROR] Falha ao atualizar mensagem: {e}")

    def has_status_changed(current, last):
        return current != last

    last_status = {
        "ip": None,
        "online": None,
        "players_online": None,
        "version": None,
        "player_names": None,
    }

    while True:
        try:
            current_ip, server_online, players_online, version, player_names = await get_current_status()

            if has_status_changed(
                (current_ip, server_online, players_online, version, player_names),
                (last_status["ip"], last_status["online"], last_status["players_online"], last_status["version"], last_status["player_names"])
            ):
                if "Anonymous Player" not in (player_names or []):

                    left_players = get_left_players(player_names, last_status["player_names"])
                    player_name = player_names[0] if player_names else None
                    update_database(player_name, server_online, players_online, left_players)

                    embed = create_embed(current_ip, server_online, players_online, version, player_names)
                    await update_discord_message(message, embed)

                    last_status.update({
                        "ip": current_ip,
                        "online": server_online,
                        "players_online": players_online,
                        "version": version,
                        "player_names": player_names,
                    })

            await asyncio.sleep(interval)
        except Exception as e:
            print(f"[ERROR] Ocorreu um erro inesperado ao atualizar a mensagem do servidor: {e}")
            await asyncio.sleep(interval)