import discord
from discord import ui
import config
from TSH.TSHObjects import Stage, State, Player

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
    def __init__(self, *, state:State):
        super().__init__(timeout=None)
        self.state:State = state
        self.confirm_message:discord.Message = None
        self.value = None
        # TODO: Add interface to handle disputes

        self.winner_select.min_values = 1
        self.winner_select.max_values = 1
        # Value is a number so that i can test with matches against myself
        self.winner_select.options = [discord.SelectOption(label=self.state.players[p].display_name, value=p, emoji="🏆") for p in range(len(self.state.players))]
    
    @ui.select(placeholder="Report Winner:")
    async def winner_select(self, interaction:discord.Interaction, select:ui.Select[ReportWinnerInput]):
        if self.confirm_message:
            return
        self.value = select.values[0]
        select.disabled = True

        # Disable selection
        await interaction.response.defer()
        original_msg:discord.InteractionMessage = await interaction.original_response()
        await original_msg.edit(view=self)

        # Create confirm or deny view
        # Get player(s) who didn't make this report.
        confirm_view:ConfirmWinner = ConfirmWinner(target_users=[u.discord_user for u in self.state.players if u.discord_user != interaction.user])
        # TODO: Create embed displaying reported score
        self.confirm_message = await interaction.followup.send(content="placeholder", view=confirm_view)

        await confirm_view.wait()

        if confirm_view.value == None:
            # Timeout
            # Re-enable select & delete reported score
            await self.confirm_message.delete()
            select.disabled = False
            self.value = None
            await original_msg.edit(view=self)
        elif confirm_view.value == False:
            # Denied
            # Dont delete denied score reports, as it makes it easier to tell what's happening to a moderator/TO when handling disputes
            # TODO: Create Embed to show disputed score
            select.disabled = False
            self.value = None
            await original_msg.edit(view=self)
            pass
        else:
            # Accepted
            await self.confirm_message.delete()
            pass

    async def interaction_check(self, interaction:discord.Interaction, /) -> bool:
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