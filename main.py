import config
from os import getenv
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from TSH import TSHCommunicator
from TSH.TSHObjects import Stage, Ruleset, State

from gamelogic import GameInstance

from views import AcceptOrDenyDuelRequest

from random import randint
import datetime
import asyncio


# Bot Setup
load_dotenv()
TOKEN = getenv("TOKEN")
intents = discord.Intents.default()
# intents.message_content = True
bot = commands.Bot(intents=intents, command_prefix=commands.when_mentioned_or("."))
# bot.tree = app_commands.CommandTree(bot)

# Globals Setup
active_instances:dict[int, GameInstance] = {}
outgoing_requests:list[discord.User] = []
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

def is_id_taken(_id:int) -> bool:
    for instID in active_instances.keys():
        if instID == _id:
            return True
    return False
def get_unique_instance_id() -> int:
    uniqueID:int = randint(1, 256)
    if len(active_instances) > 0:
        if len(active_instances) >= 256:
            print("ERROR: Couldnt find a unique instance id!")
            return None
        if is_id_taken(uniqueID):
            uniqueID = get_unique_instance_id((uniqueID+1) % 256)
            print(f"Found unique ID: #{uniqueID}")
            return uniqueID
        return None
    else:
        return uniqueID

@bot.tree.command(name='stream_match', description='Begins the stage striking process in the current channel')
@app_commands.describe(p1="Discord User of player 1", p2="Discord User of player 2")
@app_commands.default_permissions(permissions=16) # Manage Channels
async def stream_match(interaction: discord.Interaction, p1:discord.User, p2:discord.User):
    # if p1 == p2:
    #     await interaction.response.send_message(content="Both players cannot have the same user ID", ephemeral=True)
    #     return
    
    if active_instances.get(0) != None:
        await interaction.response.send_message(content="There is already a stream match instance running.", ephemeral=True)
        return

    new_state = State(tsh_data=TSHCommunicator.fetch_data())
    
    # User Error Checks
    if new_state.p1._display_name == "":
        await interaction.response.send_message(content="TSH Error: `p1` Doesn't have a name", ephemeral=True)
        return
    if new_state.p2._display_name == "":
        await interaction.response.send_message(content="TSH Error: `p2` Doesn't have a name", ephemeral=True)
        return
    
    if new_state.best_of % 2 != 1 or new_state.best_of < 1:
        await interaction.response.send_message(content="TSH Error: `best_of` must be an odd number above 0.", ephemeral=True)
        return
    
    new_state.p1.discord_user = p1
    new_state.p2.discord_user = p2
    
    TSHCommunicator.post_reset_stage_strike()
    TSHCommunicator.post_rps_win(randint(0,1))

    embed:discord.Embed = discord.Embed(title=f"Stream Match ({new_state.p1.display_name} vs {new_state.p2.display_name})",\
        description=f"( Best of {new_state.best_of} )\nPlease strike stages in the thread on this message",\
            colour=discord.Colour.red())
    
    await interaction.response.send_message(content="<@"+str(p1.id)+"> "+"<@"+str(p2.id)+">", embed=embed)

    message = await interaction.original_response()
    thread:discord.Thread = await message.create_thread(name=f"Stream Match: {new_state.p1.display_name} vs {new_state.p2.display_name}", \
        auto_archive_duration=1440, reason="Tournament Match")
    
    active_instances[0] = GameInstance(0, thread=thread, state=new_state)

    # Create run_stream_match task
    active_instances[0].async_task = asyncio.create_task(active_instances[0].run_stream_match())
    # Wait for task to be done
    while not active_instances[0].async_task.done():
        # just check in 1s intervals I GUESS IDKKK
        await asyncio.sleep(1)
    
    # Delete match after ending
    if active_instances.get(0) != None:
        active_instances.pop(0)    
    print(f"Killed match instance #{0} (Stream match)")
    
    # FIXME: this interaction has suddenly started failing for some reason??
    await message.edit(content="> Stream match has concluded.", embed=None)

@bot.tree.command(name='start_match', description='Begins the stage striking process in the current channel')
@app_commands.describe(opponent="Discord User of the player you are dueling", best_of="The maximum amount of rounds possible in the set (Must be an odd number)")
async def start_match(interaction: discord.Interaction, opponent:discord.User, best_of:int):
    # User error checks
    if opponent == interaction.user:
        await interaction.response.send_message(content="You cannot start a match against yourself.", ephemeral=True)
        return

    for user in outgoing_requests:
        if user == interaction.user:
            await interaction.response.send_message(content="You already have an outgoing request for a match.", ephemeral=True)
            return

    if best_of % 2 != 1 or best_of < 1:
        await interaction.response.send_message(content="`best_of` must be an odd number above 0.", ephemeral=True)
        return

    if best_of > config.get_max_best_of():
        await interaction.response.send_message(content=f"Sets cannot be longer than a best of {config.get_max_best_of()}", ephemeral=True)

    for instance in active_instances:
        instance = active_instances[instance]
        # Check if user sending command is already in a match
        if instance.state.p1.discord_user == interaction.user or instance.state.p2.discord_user == interaction.user:
            await interaction.response.send_message(content=f"You are already in match #{instance.ID}.", ephemeral=True)
            return

        # Check if requested opponent is already in a match
        if instance.state.p1.discord_user == opponent or instance.state.p2.discord_user == opponent:
            await interaction.response.send_message(content=f"<@{opponent.id}> is already participating in match #{instance.ID}.", ephemeral=True)
            return
    
    # Add user to pending requests list
    outgoing_requests.append(interaction.user)

    # Create embed details
    embed:discord.Embed = discord.Embed(title="Match Request", colour=discord.Colour.gold(), \
        description=f"<@{interaction.user.id}> has requested for a best of {best_of} match with you.\n(Expires in {config.get_match_request_timeout()}s)",\
            timestamp=datetime.datetime.now(datetime.UTC))
    # Create view and pass requested opponent
    view = AcceptOrDenyDuelRequest(interaction.user, opponent)
    # Send message
    await interaction.response.send_message(content=f"<@{opponent.id}>", embed=embed, view=view)
    # Wait for view to timeout or close
    await view.wait()
    # Remove user from outgoing_requests list
    outgoing_requests.remove(interaction.user)
    if view.value is None:
        # Request timed out
        embed.title = embed.title+" (Timed Out)"
        embed.description = "~~"+embed.description+"~~"
        await interaction.edit_original_response(embed=embed, view=None)
        if config.get_delete_expired_requests():
            await asyncio.sleep(10.0)
            await interaction.delete_original_response()
    elif view.value == True:
        # Opponent has accepted the duel request, begin initalizing the match

        # Create state for game instance
        new_state:State = State(best_of)
        new_state.p1.discord_user = interaction.user
        new_state.p2.discord_user = opponent

        instance_id:int = get_unique_instance_id()
        message = await interaction.original_response() # HATE. LET ME TELL YOU HOW MUCH I HAVE COME TO HATE
        thread:discord.Thread = await message.create_thread(name=f"Match #{instance_id}: {interaction.user.global_name} vs {opponent.global_name}", \
            auto_archive_duration=1440, reason="Tournament Match")
        # Create game instance and add it to active_instances[].
        active_instances[instance_id] = GameInstance(instance_id, thread=thread, state=new_state)
        
        await interaction.edit_original_response(content="**Match has now begun. Please strike stages in the newly created thread**", embed=None, view=None)
        await interaction.followup.send(content=f"-# <@{interaction.user.id}><@{opponent.id}>")
        
        # Create run_match task
        active_instances[instance_id].async_task = asyncio.create_task(active_instances[instance_id].run_match())
        # Wait for task to be done
        while not active_instances[instance_id].async_task.done():
            # just check in 1s intervals I GUESS IDKKK
            await asyncio.sleep(1)
        
        # Delete match after ending
        active_instances.pop(instance_id)
        print(f"Killed match instance #{instance_id}")

        # FIXME: this interaction has suddenly started failing for some reason??
        await message.edit(content="> Match has concluded.")
    elif view.value == False:
        await interaction.delete_original_response()
    
    try:
        # Remove user from active_requests list (just in case something went crazy wrong)
        outgoing_requests.remove(interaction.user)
    except:
        pass

@bot.tree.command(name='kill_match', description='Ends the currently running match by ID')
@app_commands.describe(match_id="The match ID to terminate")
@app_commands.default_permissions(permissions=16) # Manage Channels
async def kill_match(interaction: discord.Interaction, match_id:int):
    if active_instances.get(match_id) != None:
        await active_instances[match_id].terminate_match()
        await interaction.response.send_message(content=f"Sent termination command to Match #{match_id}.", ephemeral=True)
        return
    
    await interaction.response.send_message(content=f"There is no match with ID #{match_id}.", ephemeral=True)

bot.setup_hook = setup_hook
bot.run(TOKEN)