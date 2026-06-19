import config
from os import getenv
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from TSH import TSHCommunicator
from TSH.TSHObjects import Stage, Ruleset, State

import gamelogic
from gamelogic import GameInstance

from views import AcceptOrDenyDuelRequest

from random import randint
import datetime


# Bot Setup
load_dotenv()
TOKEN = getenv("TOKEN")
intents = discord.Intents.default()
# intents.message_content = True
bot = commands.Bot(intents=intents, command_prefix=commands.when_mentioned_or("."))
# bot.tree = app_commands.CommandTree(bot)

# Globals Setup
active_instances:list[GameInstance] = []
TSHCommunicator.fetch_data()

# Runs only once at during bot initialisation
async def setup_hook():
    print("SETUP HOOK BEGIN:")
    assert bot.user is not None
    await bot.tree.sync()
    print("END SETUP HOOK")

# Runs every time the bot connects to discord
# This can re-run if the bot loses connection somehow and reconnects.
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# Runs every time the bot sees a new message
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    
    await bot.process_commands(message)

@bot.hybrid_command()
@app_commands.default_permissions()
async def sync(ctx: commands.Context):
    """
    Syncs tree commands to discord

    Parameters
    ----------
    ctx
       The context of the command invocation
    """
    print("Recieved sync request")
    await ctx.defer(ephemeral=True)
    synced = await ctx.bot.tree.sync()
    await ctx.send(f"Synced {len(synced)} commands globally")

def get_unique_instance_id() -> int:
    uniqueID:int = randint(1, 256)
    for instance in active_instances:
        if instance.ID == uniqueID:
            uniqueID = get_unique_instance_id()
            return uniqueID

@bot.tree.command(name='stream_match', description='Begins the stage striking process in the current channel')
@app_commands.describe(p1="Discord User of player 1", p2="Discord User of player 2")
@app_commands.default_permissions()
async def stream_match(interaction: discord.Interaction, p1:discord.User, p2:discord.User):
    if p1 == p2:
        await interaction.response.send_message(content="Both players cannot have the same user ID", ephemeral=True)
        return

    gamestate = State(tsh_data=TSHCommunicator.fetch_data())
    gamestate.p1.discord_user_id = p1.id
    gamestate.p2.discord_user_id = p2.id

    TSHCommunicator.post_reset_stage_strike()
    TSHCommunicator.post_rps_win(randint(0,1))

    embed:discord.Embed = discord.Embed(title="Stream Match",\
        description="Please strike stages at http://172.26.3.130:5000/stage-strike-app",\
            colour=discord.Colour.red())
    
    await interaction.response.send_message(content="<@"+str(p1.id)+"> "+"<@"+str(p2.id)+">", embed=embed)

@bot.tree.command(name='start_match', description='Begins the stage striking process in the current channel')
@app_commands.describe(opponent="Discord User of the player you are dueling", best_of="The maximum amount of rounds possible in the set (Must be an odd number)")
async def start_match(interaction: discord.Interaction, opponent:discord.User, best_of:int):
    # User error checks
    # if opponent == interaction.user:
    #     await interaction.response.send_message(content="Cannot start: You cannot start a match against yourself.", ephemeral=True)
    #     return

    if best_of % 2 != 1 or best_of < 1:
        await interaction.response.send_message(content="Cannot start: `best_of` must be an odd number above 0.", ephemeral=True)
        return

    if best_of > config.get_max_best_of():
        await interaction.response.send_message(content=f"Cannot start: Sets cannot be longer than a best of {config.get_max_best_of}", ephemeral=True)

    for instance in active_instances:
        # Check if user sending command is already in a match
        if instance.state.p1.discord_user_id == interaction.user.id or\
            instance.state.p2.discord_user_id == interaction.user.id:
            await interaction.response.send_message(content=f"Cannot start: You are already in match #{instance.ID}.", ephemeral=True)
            return

        # Check if requested opponent is already in a match
        if instance.state.p1.discord_user_id == opponent.id or\
            instance.state.p2.discord_user_id == opponent.id:
            await interaction.response.send_message(content=f"Cannot start: <@{opponent.id}> is already participating in match #{instance.ID}.", ephemeral=True)
            return
    
    # Create embed details
    embed:discord.Embed = discord.Embed(title="Duel Request", colour=discord.Colour.gold(), \
        description=f"<@{interaction.user.id}> has requested for a best of {best_of} match with you.\n(Expires in {config.get_match_request_timeout()}s)",\
            timestamp=datetime.datetime.now(datetime.UTC))
    # Create view and pass requested opponent
    view = AcceptOrDenyDuelRequest(opponent)
    # Send message
    await interaction.response.send_message(content=f"<@{opponent.id}>", embed=embed, view=view)
    # Wait for view to timeout or close
    await view.wait()
    if view.value is None:
        embed.title = "Duel Request (Timed Out)"
        embed.description = "~~"+embed.description+"~~"
        await interaction.edit_original_response(embed=embed, view=None)
    elif view.value == True:
        message = await interaction.original_response() # HATE. LET ME TELL YOU HOW MUCH I HAVE COME TO HATE
        thread:discord.Thread = await message.create_thread(name="Match: "+interaction.user.display_name+" vs "+opponent.display_name, \
            auto_archive_duration=4320, reason="Tournament Match")
        
        await interaction.edit_original_response(content="**Match has now begun. Please strike stages in the newly created thread**", embed=None, view=None)
        await interaction.followup.send(content=f"-# <@{interaction.user.id}><@{opponent.id}>")
        
        # TODO: Create game instance and add it to active_instances[].
        await thread.send(content="TEST")

bot.setup_hook = setup_hook
bot.run(TOKEN)