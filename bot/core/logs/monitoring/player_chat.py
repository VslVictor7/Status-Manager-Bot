import os
from dotenv import load_dotenv
from .offline_player_loader import load_json

load_dotenv()

SERVER_MODE = os.getenv('SERVER_MODE', '0')

offline_players = load_json('players.json')
default_uuid = "c2e45a26339547ff86c0b3dd0c2aa2d2"

async def process_user_messages(webhook, log_line):
    try:
        if "<" not in log_line or ">" not in log_line:
            return

        ignore_patterns = [
            "[Rcon]", "Disconnecting VANILLA connection attempt",
            "rejected vanilla connections", "lost connection", "id=<null>", "legacy=false",
            "lost connection: Disconnected", "<init>"
        ]

        if any(pattern in log_line for pattern in ignore_patterns):
            return

        try:
            player_name, message = extract_player_message(log_line)
        except (ValueError, IndexError):
            return

        if player_name and message:
            await send_message_as_user(webhook, player_name, message)
        return
    except Exception as e:
        print(f"Erro ao processar evento de usuários mandando mensagens no discord: {e}")


async def send_message_as_user(webhook, username, message):
    try:
        uuid = username
        if SERVER_MODE != "0":
            for player_name, player_data in offline_players.items():
                if player_name == username and player_data["original"] == False:
                    uuid = default_uuid
        await webhook.send(
            content=message,
            username=username,
            avatar_url=f"https://mineskin.eu/helm/{uuid}"
        )
    except Exception as e:
        print(f"[BOT ERROR] Falha ao enviar mensagem como usuário: {e}")

def extract_player_message(log_line):
    try:
        start = log_line.index("<") + 1
        end = log_line.index(">")
        player_name = log_line[start:end].strip()
        message = log_line[end + 1:].strip()
        return player_name, message
    except ValueError as e:
        print(f"[BOT] Erro ao extrair nome do jogador e mensagem: {e}")
        return None, None