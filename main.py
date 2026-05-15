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

# Runs every time the bot connects to discord
# This can re-run if the bot loses connection somehow and reconnects.
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()

class Feedback(ui.Modal, title='Feedback'):
    # Our modal classes MUST subclass `discord.ui.Modal`,
    # but the title can be whatever you want.

    # This will be a short input, where the user can enter their name
    # It will also have a placeholder, as denoted by the `placeholder` kwarg.
    # By default, it is required and is a short-style input which is exactly
    # what we want.
    name = discord.ui.TextInput(
        label='Name',
        placeholder='Your name here...',
    )

    # This is a longer, paragraph style input, where user can submit feedback
    # Unlike the name, it is not required. If filled out, however, it will
    # only accept a maximum of 300 characters, as denoted by the
    # `max_length=300` kwarg.
    feedback = discord.ui.TextInput(
        label='What do you think of this new feature?',
        style=discord.TextStyle.long,
        placeholder='Type your feedback here...',
        required=False,
        max_length=300,
    )

    async def on_submit(self, interaction: discord.Interaction):
        print(self.feedback.value)
        print(self.name.value)
        await interaction.response.send_message(f'Thanks for your feedback, {self.name.value}!', ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)

        # Make sure we know what the error actually is
        traceback.print_exception(type(error), error, error.__traceback__)

class ConfirmView(ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        print(interaction.user.id)
        await interaction.response.edit_message(content='Confirmed', view=None)
        self.value = True
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content='Cancelled', view=None)
        self.value = False
        self.stop()

@bot.tree.command(name='init', description='Begins the stage striking process in the current channel')
@app_commands.describe(stream_match="Connects the banning interface to the stream tool. Can only be used by stream moderators.")
async def init(interaction: discord.Interaction, stream_match:bool=False):
    user = interaction.user
    if stream_match and (user.permissions.administrator or user.get_role()):
        pass

    view = ConfirmView()
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