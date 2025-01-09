import os
import json
import requests
import discord
import pytz
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

JSON_PATH = os.getenv('JSON_PATH')
OFFLINE_PLAYERS_PATH = os.getenv('OFFLINE_PLAYERS_PATH')
SERVER_MODE = os.getenv('SERVER_MODE', '0')

uuid_cache = {}

def load_json(file_name):
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'json', file_name)

        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError as e:
        print(f"[BOT ERROR] Arquivo não encontrado: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"[BOT ERROR] Erro ao decodificar o arquivo: {e}")
        return {}

offline_players = load_json('players.json')

def get_all_play_times(directory):
    try:
        if not os.path.exists(directory):
            print("Erro: O diretório especificado não foi encontrado.")
            return []

        player_times = []

        for file_name in os.listdir(directory):
            if file_name.endswith(".json"):  # Considera apenas arquivos JSON
                file_path = os.path.join(directory, file_name)

                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        stats = json.load(file)

                    # Extrai tempo de jogo do JSON
                    custom_stats = stats.get("stats", {}).get("minecraft:custom", {})
                    play_time = custom_stats.get("minecraft:play_time", 0) // 20  # Tempo em segundos

                    # Adiciona o UUID (presumindo que o nome do arquivo é o UUID do jogador)
                    uuid = os.path.splitext(file_name)[0]
                    player_times.append((uuid, play_time))
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Erro ao processar o arquivo {file_name}: {e}")

        return player_times

    except Exception as e:
        print(f"Erro ao obter tempo de jogo dos jogadores: {e}")
        return []


def display_top_players(player_times, top_n=5):
    try:
        sorted_players = sorted(player_times, key=lambda x: x[1], reverse=True)
        return sorted_players[:top_n]
    except Exception as e:
        print(f"Erro ao classificar os jogadores: {e}")
        return []


async def get_username_from_uuid(uuid):
    try:
        if SERVER_MODE == "1":
            for username, player_data in offline_players.items():
                if player_data["uuid"] == uuid:
                    return username
            return None

        if uuid in uuid_cache:
            return uuid_cache[uuid]

        response = requests.get(f"https://api.minetools.eu/uuid/{uuid}")
        response.raise_for_status()

        data = response.json()
        if not data or "name" not in data:
            raise ValueError(f"O UUID '{uuid}' não foi encontrado na API Mojang.")

        username = data["name"]
        uuid_cache[uuid] = username
        return username

    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar a API Mojang para o UUID '{uuid}': {e}")
        return "Nome não encontrado"
    except ValueError as e:
        print(e)
        return "Nome não encontrado"


async def raking_players():
    try:
        player_times = get_all_play_times(JSON_PATH)

        if player_times:

            sao_paulo_tz = pytz.timezone('America/Sao_Paulo')
            current_time = datetime.now(sao_paulo_tz)

            top_players = display_top_players(player_times)

            embed = discord.Embed(title="Ranking dos Jogadores com Mais Tempo de Jogo", color=discord.Color.yellow())

            medal_emojis = {1: "🥇", 2: "🥈", 3: "🥉"}

            for rank, (uuid, play_time) in enumerate(top_players, start=1):
                username = await get_username_from_uuid(uuid)
                hours, minutes, seconds = play_time // 3600, (play_time % 3600) // 60, play_time % 60

                player_info = f"Tempo jogado: {hours}h {minutes}m {seconds}s"

                medal_emoji = medal_emojis.get(rank, "")

                embed.add_field(name=f"{rank}º Lugar {medal_emoji}",value=f"Nome: {username}\n{player_info}", inline=False)

            embed.timestamp = current_time

            return embed
        else:
            return None

    except Exception as e:
        print(f"Erro ao gerar ranking dos jogadores: {e}")
        return None