import discord
from discord import ui
import config
from TSH.TSHObjects import Stage

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