import config
from os import getenv
import discord
from discord import app_commands
from discord import ui
from dotenv import load_dotenv

import TSHCommunicator

load_dotenv()
TOKEN = getenv("TOKEN")

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
bot.tree = app_commands.CommandTree(bot)

TSHCommunicator.fetch_data()
current_ruleset = TSHCommunicator.current_ruleset
current_state = TSHCommunicator.current_state

# Runs only once at during bot initialisation
async def setup_hook():
    print("SETUP HOOK BEGIN:")
    assert bot.user is not None
    assert config.get_stream_manager_role_id() != 0

# Runs every time the bot connects to discord
# This can re-run if the bot loses connection somehow and reconnects.
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()

class StageButton(discord.ui.Button):
    display_name:str = "Stage"
    stage_object:dict

    def __init__(self, stage_object:dict, row:int=0):
        self.stage_object = stage_object
        self.display_name = stage_object['display_name']
        super().__init__(label=self.display_name, row=row)
    
    def style(self) -> discord.ButtonStyle:
        return discord.ButtonStyle.gray

    async def callback(self, interaction:discord.Interaction) -> None:
        TSHCommunicator.request_strike_stage(self.stage_object)
        await interaction.response.edit_message(view=self.view)

class ConfirmView(ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

        from math import floor
        for i in range(len(current_ruleset.neutralStages) - 1):
            self.add_item(StageButton(current_ruleset.neutralStages[i], floor(float(i)/5.0)))
        for i in range(len(current_ruleset.counterpickStages) - 1):
            self.add_item(StageButton(current_ruleset.counterpickStages[i], floor(float(i + len(current_ruleset.neutralStages))/5.0)))
    
    
    confirm_row:int = min(len(current_ruleset.neutralStages), 4)
    
    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green, row=confirm_row)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        print(interaction.user.id)
        await interaction.response.edit_message(content='Confirmed', view=None)
        self.value = True
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.grey, row=confirm_row)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content='Cancelled', view=None)
        self.value = False
        self.stop()

@bot.tree.command(name='init', description='Begins the stage striking process in the current channel')
@app_commands.describe(stream_match="Connects the banning interface to the stream tool. Can only be used by stream moderators.")
async def init(interaction: discord.Interaction, stream_match:bool=False):
    user = interaction.user
    if stream_match and (user.permissions.administrator or user.get_role(config.get_stream_manager_role_id())):
        pass

    view = ConfirmView()
    view.timeout = None
    await interaction.response.send_message('erm', view=view)
    await view.wait()
    if view.value is None:
        print('Timed out')
    elif view.value:
        print('Confirmed')
    else:
        print('Cancelled')
    # await interaction.response.send_modal(Feedback())

bot.setup_hook = setup_hook
bot.run(TOKEN)