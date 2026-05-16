import config
from os import getenv
import discord
from discord import app_commands
from discord import ui
from dotenv import load_dotenv

import random

import TSHCommunicator
from TSHObjects import Stage

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
    def __init__(self, stage_object:Stage, row:int=0):
        self.stage:Stage = stage_object
        super().__init__(label=self.stage.display_name, row=row, style=self.get_style(), disabled=self.get_disabled())
    
    def get_style(self) -> discord.ButtonStyle:
        if self.stage.codename in current_state.get_all_striked_stage_codenames():
            return discord.ButtonStyle.red
        else:
            return discord.ButtonStyle.gray
    
    def get_disabled(self) -> bool:
        if self.stage.codename in current_state.get_confirmed_striked_stage_codenames():
            return True
        if self.stage.codename in current_state.get_pending_striked_stage_codenames():
            return False
        return not current_state.can_strike(current_ruleset)
    
    def update_all_stage_buttons(self):
        for child in self.view.children:
            if isinstance(child, StageButton):
                child.style = child.get_style()
                child.disabled = child.get_disabled()
        
    async def callback(self, interaction:discord.Interaction) -> None:
        TSHCommunicator.request_strike_stage(self.stage)
        self.view.update_buttons()
        await interaction.response.edit_message(view=self.view)

class ConfirmView(ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

        from math import floor
        for i in range(len(current_ruleset.neutralStages)):
            self.add_item(StageButton(current_ruleset.neutralStages[i], floor(float(i)/5.0)))
        
        if current_state.currGame == 0:
            return
        
        for i in range(len(current_ruleset.counterpickStages)):
            self.add_item(StageButton(current_ruleset.counterpickStages[i], floor(float(i + len(current_ruleset.neutralStages))/5.0)))
    
    def update_buttons(self):
        for child in self.children:
            child:discord.Button = child
            if isinstance(child, StageButton):
                child:StageButton = child
                child.style = child.get_style()
                child.disabled = child.get_disabled()


    confirm_row:int = min(len(current_ruleset.neutralStages), 4)

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green, row=confirm_row)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        TSHCommunicator.post_confirm_stage_strike()
        self.update_buttons()
        await interaction.response.edit_message(content=current_state.currPlayer.display_name, view=self)

    @discord.ui.button(label='Undo', style=discord.ButtonStyle.grey, row=confirm_row)
    async def undo(self, interaction: discord.Interaction, button: discord.ui.Button):
        TSHCommunicator.post_stage_strike_undo()
        self.update_buttons()
        await interaction.response.edit_message(view=self)
    
    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.grey, row=confirm_row)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        TSHCommunicator.post_reset_stage_strike()
        await interaction.response.edit_message(content='Cancelled', view=None)
        self.value = False
        self.stop()
    

@bot.tree.command(name='init', description='Begins the stage striking process in the current channel')
@app_commands.describe(stream_match="Connects the banning interface to the stream tool. Can only be used by stream moderators.")
async def init(interaction: discord.Interaction, stream_match:bool=False):
    user = interaction.user
    if stream_match and (user.permissions.administrator or user.get_role(config.get_stream_manager_role_id())):
        pass

    TSHCommunicator.post_reset_stage_strike()
    TSHCommunicator.post_rps_win(random.randint(0,1))
    view = ConfirmView()
    view.timeout = None
    await interaction.response.send_message(current_state.currPlayer.display_name, view=view)
    await view.wait()
    if view.value is None:
        print('Timed out')
    elif view.value:
        print('Selected Stage: ' + str(view.value))
    else:
        print('Cancelled')
    # await interaction.response.send_modal(Feedback())

bot.setup_hook = setup_hook
bot.run(TOKEN)