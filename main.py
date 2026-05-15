import config
from os import getenv
import discord
from discord import app_commands
from discord import ui
from dotenv import load_dotenv

load_dotenv()

TOKEN = getenv("TOKEN")
SERVER_IP = "localhost"
SERVER_PORT = 5000
SERVER_URL = "http://"+SERVER_IP+":"+str(SERVER_PORT)

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
bot.tree = app_commands.CommandTree(bot)


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
    display_name = "Stage"
    on_pressed_callback:callable
    stage_object:dict

    def __init__(self, stage_object:dict={}, on_pressed_callback:callable=()):
        self.stage_object = stage_object
        self.stage_object['display_name'] = "STAGE_NAME" # TEMP
        self.display_name = stage_object['display_name']
        self.on_pressed_callback = on_pressed_callback
        super().__init__(label="Stage",row=0)
    
    async def callback(self, interaction:discord.Interaction) -> None:
        self.style = discord.ButtonStyle.red
        await interaction.response.edit_message(view=self.view)

class ConfirmView(ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

        self.add_item(StageButton(on_pressed_callback=self.on_ban_pressed))
        self.add_item(StageButton(on_pressed_callback=self.on_ban_pressed))
    
    async def on_ban_pressed(interaction:discord.Interaction, stage_object:dict):
        await interaction.response.edit_message(content='Banned '+stage_object['display_name'], view=None)

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green, row=1)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        print(interaction.user.id)
        await interaction.response.edit_message(content='Confirmed', view=None)
        self.value = True
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.grey, row=1)
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
    await interaction.response.send_message('erm', view=view, ephemeral=True)
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