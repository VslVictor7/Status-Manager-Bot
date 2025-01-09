import discord
import os
import pytz
import json
from dotenv import load_dotenv
from datetime import datetime
from mcstatus import JavaServer
from utils import player_json
from utils import player_json
from utils import ranking_players

load_dotenv()

JSON_PATH = os.getenv('JSON_PATH')
IP_ADRESS = os.getenv('MINECRAFT_SERVER')
PORT = os.getenv('MINECRAFT_PORT')
SERVER_MODE = os.getenv('SERVER_MODE', '0')

def create_embed(title, description, color):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    embed.timestamp = datetime.now(pytz.timezone("America/Sao_Paulo"))
    return embed

async def setup_commands(bot):

    @bot.tree.command(name="uptime", description="Mostra o tempo que o servidor está online.")
    async def uptime(interaction: discord.Interaction):
        if bot.uptime_start:
            current_time = datetime.now(pytz.timezone('America/Sao_Paulo'))
            uptime_duration = current_time - bot.uptime_start
            hours, remainder = divmod(uptime_duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            uptime_message = f"O servidor está online há {hours} horas, {minutes} minutos e {seconds} segundos."
            embed = create_embed("Uptime do Servidor", uptime_message, 0x7289DA)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("O servidor está offline no momento.", ephemeral=True)

    @bot.tree.command(name="limpar_dms", description="Apaga mensagens do bot na DM atual.")
    async def limpar_dms(interaction: discord.Interaction):
        if isinstance(interaction.channel, discord.DMChannel):
            await interaction.response.defer(ephemeral=True)
            count = 0
            async for message in interaction.channel.history(limit=100):
                if message.author == bot.user:
                    await message.delete()
                    count += 1

            # Envia a resposta final
            await interaction.followup.send(f"{count} mensagens apagadas.")
        else:
            # Resposta caso o comando não esteja em uma DM
            await interaction.response.send_message(
                "Este comando só funciona em mensagens diretas (DMs).",
                ephemeral=True,
            )

    @bot.tree.command(name="limpar", description="Apaga mensagens do canal atual no servidor.")
    async def limpar(interaction: discord.Interaction, quantidade: int):
        if isinstance(interaction.channel, discord.TextChannel):
            if not interaction.user.guild_permissions.manage_messages:
                await interaction.response.send_message(
                    "Você não tem permissão para usar este comando.",
                    ephemeral=True
                )
                return

            if quantidade < 1:
                await interaction.response.send_message(
                    "Por favor, insira um número válido de mensagens para apagar (no mínimo 1).",
                    ephemeral=True
                )
                return

            await interaction.response.defer(ephemeral=True)

            try:
                deleted_messages = await interaction.channel.purge(limit=quantidade)
                await interaction.followup.send(
                    f"{len(deleted_messages)} mensagens apagadas com sucesso!",
                    ephemeral=True
                )
            except discord.Forbidden:
                await interaction.followup.send(
                    "O bot não tem permissão para apagar mensagens neste canal.",
                    ephemeral=True
                )
            except discord.HTTPException as e:
                await interaction.followup.send(
                    f"Ocorreu um erro ao tentar apagar as mensagens: {e}",
                    ephemeral=True
                )
        else:
            # Caso o comando seja usado em uma DM
            await interaction.response.send_message(
                "Este comando só pode ser usado em canais de texto do servidor.",
                ephemeral=True
            )


    @bot.tree.command(name="ping", description="Verifica o ping do servidor Minecraft")
    async def ping(interaction: discord.Interaction):
        try:
            server = JavaServer.lookup(f"{IP_ADRESS}:{PORT}")
            latency = server.ping()
            latency = round(latency, 2)
            latency_text = f"{latency} ms"
            embed = create_embed("Latência do Servidor", latency_text, 0x7289DA)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            latency_text = f"Erro ao obter latência: {e}"
            embed = create_embed("Latência do Servidor", latency_text, 0x7289DA)
            await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="stats", description="Mostra estatísticas do jogador Minecraft.")
    async def player_information(interaction: discord.Interaction, username: str):

        try:
            uuid = None
            if SERVER_MODE == "1":
                player_data = offline_players.get(username)
                if not player_data:
                    await interaction.response.send_message(f"Jogador '{username}' não encontrado no modo offline.", ephemeral=True)
                    return
                uuid = player_data.get("uuid")

            else:
                uuid = player_json.get_uuid_from_username(username)
                if not uuid:
                    await interaction.response.send_message(f"Nome de usuário '{username}' não encontrado ou inválido.", ephemeral=True)
                    return

            stats_path = f"{JSON_PATH}{uuid}.json"
            stats_message = player_json.player_stats(stats_path, username)

            if not stats_message:
                raise ValueError(f"Não foi possível gerar estatísticas para o jogador '{username}'. Certifique-se de escrever o nome de usuário corretamente!")

            await interaction.response.send_message(embed=stats_message)

        except FileNotFoundError:
            await interaction.response.send_message(
                f"Arquivo de estatísticas para {username} não encontrado. Certifique-se de escrever corretamente o nome de usuário!",
                ephemeral=True
            )
        except RuntimeError as e:
            await interaction.response.send_message(
                f"Ocorreu um erro ao acessar a API Mojang: {e}",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"Ocorreu um erro inesperado: {e}",
                ephemeral=True
            )

    @bot.tree.command(name="ranking", description="Mostra ranking do jogador que tem o maior tempo de jogo do servidor.")
    async def player_ranking(interaction: discord.Interaction):
        embed = await ranking_players.raking_players()

        if embed:
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Não há jogadores no ranking ou ocorreu um erro.", ephemeral=True)

    @bot.tree.command(name="help", description="Exibe a lista de comandos disponíveis.")
    async def help_command(interaction: discord.Interaction):
        embed = create_embed(
            title="Lista de Comandos",
            description="Aqui estão os comandos disponíveis no bot:",
            color=0x7289DA
        )
        embed.add_field(
            name="/uptime",
            value="Mostra o tempo que o servidor está online.",
            inline=False
        )
        embed.add_field(
            name="/ping",
            value="Verifica o ping do servidor Minecraft.",
            inline=False
        )
        embed.add_field(
            name="/stats <username>",
            value="Mostra estatísticas do jogador Minecraft com base no nome de usuário.",
            inline=False
        )
        embed.add_field(
            name="/ranking",
            value="Mostra estatísticas do jogadores em formato de ranking para mostrar os top 5 jogadores com mais tempo de jogo.",
            inline=False
        )
        embed.add_field(
            name="/help",
            value="Exibe esta lista de comandos.",
            inline=False
        )
        embed.add_field(
            name="/limpar",
            value="Limpa o chat do canal onde o comando vai ser feito.",
            inline=False
        )
        embed.add_field(
            name="/limpar_dms",
            value="Limpa a dm do bot, comando deve ser feito na dm e não chat normal.",
            inline=False
        )
        embed.set_footer(text="Utilize os comandos para explorar as funcionalidades do bot.")

        await interaction.response.send_message(embed=embed)


def load_json(file_name):
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'utils', 'json', file_name)

        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError as e:
        print(f"[BOT ERROR] Arquivo não encontrado: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"[BOT ERROR] Erro ao decodificar o arquivo: {e}")
        return {}

offline_players = load_json('players.json')