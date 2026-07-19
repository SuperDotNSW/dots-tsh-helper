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
    def __init__(self, target_user:discord.User, opponent=discord.User):
        super().__init__(timeout=config.get_match_request_timeout())
        self.opponent = opponent
        self.target_user = target_user
        self.value = None
    
    @ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction:discord.Interaction, button:ui.button[AcceptOrDenyDuelRequest]):
        if interaction.user != self.opponent:
            return
        
        await interaction.response.edit_message(content="`Match Request Accepted! Starting new match instance...`", embed=None, view=None)
        self.value = True
        self.stop()
    
    @ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction:discord.Interaction, button:ui.button[AcceptOrDenyDuelRequest]):
        # Acks the request and returns False
        self.value = False
        self.stop()
    
    async def interaction_check(self, interaction:discord.Interaction, /) -> bool:
        return interaction.user == self.opponent or interaction.user == self.target_user

class StageInputBase(ui.View):
    def __init__(self, *, placeholder:str="UNSET", emoji:str="", available_stages:list[Stage], target_user:discord.User):
        super().__init__(timeout=None)
        self.values:list[str] = []
        self.target_user:discord.User = target_user

        # Define select menu
        self.selector.min_values = 1
        self.selector.max_values = 1
        self.selector.options = [discord.SelectOption(label=stage.display_name, value=stage.codename, emoji=emoji) for stage in available_stages]
        self.selector.placeholder = f"({self.target_user.display_name}) {placeholder}:"
    
    @ui.select()
    async def selector(self, interaction:discord.Interaction, select:ui.Select[StageBanningInput]):
        self.values = select.values
        select.disabled = True
        select.placeholder = f"Thinking..."
        await interaction.response.edit_message(view=self)
        self.stop()
    
    async def interaction_check(self, interaction:discord.Interaction) -> bool:
        return interaction.user == self.target_user

class StageBanningInput(StageInputBase):
    def __init__(self, ban_count:int, available_stages:list[Stage], target_user:discord.User):
        super().__init__(placeholder=f"Ban {ban_count} Stage(s)", available_stages=available_stages, target_user=target_user, emoji="❌")
        self.selector.min_values = ban_count
        self.selector.max_values = ban_count

class StageSelectInput(StageInputBase):
    def __init__(self, available_stages:list[Stage], target_user:discord.User):
        super().__init__(placeholder="Select Stage", available_stages=available_stages, target_user=target_user, emoji="➡️")
        self.selector.min_values = 1
        self.selector.max_values = 1

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

        # If stream manager requested it, instantly accept
        if config.is_user_id_admin(interaction.user.id):
            # Accepted
            if self.confirm_message:
                await self.confirm_message.delete()
            await original_msg.edit(view=None)
            self.stop()
        else:
            # Create confirm or deny view
            # Get player(s) who didn't make this report.
            target_users = [u.discord_user for u in self.state.players if u.discord_user != interaction.user]
            # Get the reported winner
            reported_winner = self.state.players[self.value]
            # Create the view
            confirm_view:ConfirmWinner = ConfirmWinner(target_users=target_users)
            # Create the embed
            confirm_embed:BaseEmbed = BaseEmbed(instance_info=self.instance_info)
            confirm_embed.colour = discord.Colour.dark_green()
            confirm_embed.title = "Reported Winner:"
            confirm_embed.description = f"{interaction.user.mention} reported {reported_winner.discord_user.mention} won."
            confirm_embed.set_thumbnail(url=reported_winner.discord_user.avatar.url)

            self.confirm_message = await interaction.followup.send(embed=confirm_embed, view=confirm_view)

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

                await self.confirm_message.edit(embed=embed, view=None)
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
        if config.is_user_id_admin(interaction.user.id):
            return True
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
        users_str:str = ""
        for user in self.target_users:
            users_str = users_str + user.display_name + ", "
        users_str = users_str.removesuffix(", ")
        self.accept_button.label = f"Accept ({users_str})"

    @ui.button(
        label="Accept",
        style=discord.ButtonStyle.green
    )
    async def accept_button(self, interaction:discord.Interaction, button:ui.Button[ConfirmWinner]):
        # Instant accept if admin inputs
        if config.is_user_id_admin(interaction.user.id):
            self.value = True
            await interaction.response.edit_message(view=None)
            self.stop()
            return
        
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
        if config.is_user_id_admin(interaction.user.id):
            return True
        for user in self.target_users:
            if user == interaction.user:
                return True
        return False

class ConfirmHostView(ui.View):
    def __init__(self, target_users:list[discord.User]):
        super().__init__(timeout=None)
        self.target_users:list[discord.User] = target_users
        self.accepted_users:list[discord.User] = []
        self.value = None

        # HACK: To allow 1v1's with myself for testing
        if self.target_users.count(target_users[0]) > 1:
            self.target_users.remove(target_users[0])
        
        self.update_button_label()

        if len(self.target_users) == 0:
            self.value = True
            self.stop()
        
    
    def update_button_label(self):
        self.accept_button.label = f"Connected & Ready ({len(self.accepted_users)}/{len(self.target_users)})"

    @ui.button(
        label="Ready",
        style=discord.ButtonStyle.green
    )
    async def accept_button(self, interaction:discord.Interaction, button:ui.Button[ConfirmHost]):
        if interaction.user in self.accepted_users:
            self.accepted_users.remove(interaction.user)
            self.update_button_label()
            await interaction.response.edit_message(view=self)
        else:
            self.accepted_users.append(interaction.user)
            if len(self.accepted_users) >= len(self.target_users):
                self.value = True
                await interaction.response.edit_message(view=None)
                self.stop()
            else:
                self.update_button_label()
                await interaction.response.edit_message(view=self)
    
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
        subtitle:str
        if stage.neutral:
            subtitle = "Neutral Stage"
        else:
            subtitle = "Counterpick Stage"
        self.description = f"{self.stage.display_name}\n-# {subtitle}"

        self.add_field(name="", value=f"-# To queue the map in-game, use the chat command:\n```!queue {self.stage.display_name.lower()}```")

class GameCountEmbed(BaseEmbed):
    """
    Creates an embed that displays the game count and best of
    """
    def __init__(self, instance_info:InstanceInfo, state:State):
        super().__init__(instance_info=instance_info)
        self.title = f"Game {state.currGame+1}/{state.best_of}"
        self.description = f"# {state.get_games_won(state.p1)} - {state.get_games_won(state.p2)}"
        self.add_field(name=f"Best of: {state.best_of}", value=f"-# {state.p1.discord_user.mention} vs {state.p2.discord_user.mention}", inline=False)
        for player in state.players:
            if state.get_games_won(player) >= state.get_games_to_win():
                self.title = f"Match Finished!"
                self.colour = discord.Colour.gold()
                self.set_thumbnail(url=player.discord_user.avatar.url)
                self.description = self.description + f"\n### Winner: {player.discord_user.mention}"
                self.add_field(name="", value="Please report your scores into the start.gg bracket (if applicable)", inline=False)

class ConfirmHostEmbed(BaseEmbed):
    def __init__(self, instance_info:InstanceInfo, state:State):
        super().__init__(instance_info=instance_info)
        self.title = f"Setup Match"
        self.description = f"**MAKE SURE YOU HAVE CHECKED IN ON STARTGG**\n\n\
            Please decide on a host and connect to a lobby.\n\
            Once in the playground, click the 'Connected & Ready' button.\n\n\
                Click the button again to unready."
        self.colour = discord.Colour.blurple()
        self.add_field(
            name="Hosting Guide:",
            value="[How to Host a 1v1](<https://docs.google.com/document/d/1ORMaS7vzbnZR4slmFtZGiRg6U3JuhlZ4wKSnVSkfmVs/edit?usp=sharing>)"
        )
                
def stage_to_file(stage:Stage) -> File:
    return File(fp=TSHCommunicator.SHARE.base_dir+stage.icon_path.removeprefix("."), filename=path.basename(stage.icon_path))