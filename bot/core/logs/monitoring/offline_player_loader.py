import json
import os

def load_json(file_name):
    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        file_path = os.path.join(base_dir, 'core', 'utils', 'json', file_name)

        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError as e:
        print(f"[BOT ERROR] Arquivo não encontrado: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"[BOT ERROR] Erro ao decodificar o arquivo: {e}")
        return {}