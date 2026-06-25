import discord
from discord import ui, File
import config
from TSH.TSHObjects import Stage, State, Player
from TSH import TSHCommunicator
import datetime
from os import path

# Code smell
class InstanceInfo():
    def __init__(self, ID:int, state:State):
        self.ID:int = ID
        self.state:State = state

##### VIEWS #####
class AcceptOrDenyDuelRequest(ui.View):
    def __init__(self, opponent=discord.User):
        super().__init__(timeout=config.get_match_request_timeout())
        self.opponent = opponent
        self.value = None
    
    @ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction:discord.Interaction, button:ui.button[AcceptOrDenyDuelRequest]):
        if interaction.user != self.opponent:
            return
        
        await interaction.response.edit_message(content="`Match Request Accepted! Starting new match instance...`", embed=None, view=None)
        self.value = True
        self.stop()
    
    async def interaction_check(self, interaction:discord.Interaction, /) -> bool:
        return interaction.user == self.opponent

class StageBanningInput(ui.View):
    def __init__(self, *, ban_count:int, available_stages:list[Stage], target_user:discord.User):
        super().__init__(timeout=None)
        self.values:list[str] = []
        self.ban_count:int = ban_count
        self.target_user:discord.User = target_user

        # Define select menu
        self.ban_selector.min_values = ban_count
        self.ban_selector.max_values = ban_count
        self.ban_selector.options = [discord.SelectOption(label=stage.display_name, value=stage.codename, emoji="❌") for stage in available_stages]
        self.ban_selector.placeholder = f"({self.target_user.display_name}) Select Bans:"
    
    @ui.select()
    async def ban_selector(self, interaction:discord.Interaction, select:ui.Select[StageBanningInput]):
        self.values = select.values
        await interaction.response.edit_message(view=None)
        self.stop()

    async def interaction_check(self, interaction:discord.Interaction) -> bool:
        return interaction.user == self.target_user

class ReportWinnerInput(ui.View):
    def __init__(self, *, instance_info:InstanceInfo):
        super().__init__(timeout=None)
        self.instance_info = instance_info
        self.state:State = instance_info.state
        self.confirm_message:discord.Message = None
        self.thinking = False
        self.value = None

        self.winner_select.min_values = 1
        self.winner_select.max_values = 1
        # Value is a number so that i can test with matches against myself 
        # (this makes the rest of the code harder to read and more annoying to write but whatever)
        self.winner_select.options = [discord.SelectOption(label=self.state.players[p].display_name, value=p, emoji="🏆") for p in range(len(self.state.players))]
    
    @ui.select(placeholder="Report Winner:")
    async def winner_select(self, interaction:discord.Interaction, select:ui.Select[ReportWinnerInput]):
        if self.thinking:
            return
        self.thinking = True
        self.value = int(select.values[0])
        select.disabled = True

        # Disable selection
        await interaction.response.defer()
        original_msg:discord.InteractionMessage = await interaction.original_response()
        await original_msg.edit(view=self)

        # Create confirm or deny view
        # Get player(s) who didn't make this report.
        confirm_view:ConfirmWinner = ConfirmWinner(target_users=[u.discord_user for u in self.state.players if u.discord_user != interaction.user])
        # TODO: Create embed displaying reported score
        self.confirm_message = await interaction.followup.send(content=self.state.players[self.value].display_name, view=confirm_view)

        await confirm_view.wait()

        if confirm_view.value == None:
            # Timeout
            # Re-enable select & delete reported score
            await self.confirm_message.delete()
            select.disabled = False
            self.value = None
            await original_msg.edit(view=self)
            await original_msg.reply(content="> Timed out: Please report a new winner.", delete_after=10.0)
        elif confirm_view.value == False:
            # Denied
            # Dont delete denied score reports, as it makes it easier to tell what's happening to a moderator/TO when handling disputes
            embed:discord.Embed = BaseEmbed(instance_info=self.instance_info)
            embed.colour = discord.Colour.red()
            embed.set_author(name=confirm_view.disputed_user.global_name, icon_url=confirm_view.disputed_user.display_avatar.url)
            embed.title = f"Score Disputed"
            embed.description = f"The reported winner was disputed."
            embed.add_field(name="Reported Winner:", value=f"<@{self.state.players[self.value].discord_user.id}>")
            embed.add_field(name="Reported by:", value=f"<@{interaction.user.id}>")
            embed.add_field(name="\u200b", value="If an agreement cannot be reached, please contact a Tournament Organiser", inline=False)

            await self.confirm_message.edit(content=None, embed=embed, view=None)
            self.confirm_message = None

            self.value = None
            select.disabled = False
            await original_msg.edit(view=self)
            await original_msg.reply(content=f"<@{self.state.p1.discord_user.id}><@{self.state.p2.discord_user.id}>\n\
                > Please report a new winner.", delete_after=10.0)
        else:
            # Accepted
            await self.confirm_message.delete()
            await original_msg.edit(view=None)
            self.stop()
        self.thinking = False

    async def interaction_check(self, interaction:discord.Interaction, /) -> bool:
        if self.thinking:
            return False
        return interaction.user == self.state.p1.discord_user or interaction.user == self.state.p2.discord_user


class ConfirmWinner(ui.View):
    def __init__(self, *, target_users:list[discord.User]):
        super().__init__(timeout=30)
        self.target_users:list[discord.User] = target_users
        self.accepted_users:list[discord.User] = []
        self.disputed_user:discord.User = None
        self.value = None

        self.update_button_label()

        if len(self.target_users) == 0:
            self.value = True
            self.stop()
    
    def update_button_label(self):
        self.accept_button.label = f"Accept ({len(self.accepted_users)}/{len(self.target_users)})"

    @ui.button(
        label="Accept",
        style=discord.ButtonStyle.green
    )
    async def accept_button(self, interaction:discord.Interaction, button:ui.Button[ConfirmWinner]):
        if interaction.user in self.accepted_users:
            await interaction.response.send_message(content="You have already accepted the result", ephemeral=True)
        else:
            self.accepted_users.append(interaction.user)
            if len(self.accepted_users) >= len(self.target_users):
                self.value = True
                await interaction.response.edit_message(view=None)
                self.stop()
            else:
                self.update_button_label()
                await interaction.response.edit_message(view=self)

    @ui.button(
        label="Refute",
        style=discord.ButtonStyle.danger
    )
    async def deny_button(self, interaction:discord.Interaction, button:ui.Button[ConfirmWinner]):
        self.value = False
        self.disputed_user = interaction.user
        await interaction.response.defer()
        self.stop()

    async def interaction_check(self, interaction:discord.Interaction, /) -> bool:
        for user in self.target_users:
            if user == interaction.user:
                return True
        return False

##### EMBEDS #####
class BaseEmbed(discord.Embed):
    """
    Creates an embed that has timestamp and game ID in the footer by default
    """
    def __init__(self, instance_info:InstanceInfo):
        super().__init__(timestamp=datetime.datetime.now(datetime.UTC))
        self.set_footer(text=f"#{instance_info.ID}")
        self.instance_info = instance_info
        self.state = instance_info.state

class SelectedStageEmbed(BaseEmbed):
    """
    Creates an embed to display the selected stage of the current round
    """
    def __init__(self, instance_info:InstanceInfo, stage:Stage):
        super().__init__(instance_info=instance_info)
        self.stage:Stage = stage
        self.file:File = stage_to_file(stage)

        self.colour = discord.Colour.green()
        self.set_image(url=self.file.uri)
        self.title = f"Game {self.state.currGame+1}:"
        self.description = f"{self.stage.display_name}"

class GameCountEmbed(BaseEmbed):
    """
    Creates an embed that displays the game count and best of
    """
    def __init__(self, instance_info:InstanceInfo, state:State):
        super().__init__(instance_info=instance_info)
        self.title = f"Game {state.currGame+1}/{state.best_of}"
        self.description = f"# {state.get_games_won(state.p1)} - {state.get_games_won(state.p2)}"
        self.add_field(name=f"Best of: {state.best_of}", value=f"{state.p1.discord_user.mention} vs {state.p2.discord_user.mention}")
        if state.get_games_won(state.p1) >= state.get_games_to_win() or state.get_games_won(state.p2) >= state.get_games_to_win():
            self.colour = discord.Colour.gold()

def stage_to_file(stage:Stage) -> File:
    return File(fp=TSHCommunicator.SHARE.base_dir+stage.icon_path.removeprefix("."), filename=path.basename(stage.icon_path))