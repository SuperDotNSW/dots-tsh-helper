import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Runs only once at during bot initialisation
async def setup_hook():
    pass

# Runs every time the bot connects to discord
# This can re-run if the bot loses connection somehow and reconnects.
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()

@bot.tree.command(name='echo', description='Echos a message')
@app_commands.describe(message='The message to echo')
async def echo(interaction: discord.Interaction, message:str):
    await interaction.response.send_message(message)

bot.setup_hook = setup_hook
bot.run(TOKEN)