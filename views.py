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
        if interaction.user != self.opponent:
            return False
        else:
            return True

class StageBanningInput(ui.View):
    def __init__(self, *, ban_count:int, available_stages:list[Stage], target_user:discord.User):
        super().__init__(timeout=None)
        self.values:list[str] = []
        self.ban_count:int = ban_count
        self.target_user:discord.User = target_user

        # Define select menu
        self.ban_selector.min_values = ban_count
        self.ban_selector.max_values = ban_count
        self.ban_selector.options = [discord.SelectOption(label=stage.display_name, value=stage.codename) for stage in available_stages]
        print(f"{self.target_user.display_name}")
        self.ban_selector.placeholder = f"({self.target_user.display_name}) Select Bans:"
    
    @ui.select()
    async def ban_selector(self, interaction:discord.Interaction, select:ui.Select[StageBanningInput]):
        print(f"Requested ban: {select.values}")
        self.values = select.values
        await interaction.response.edit_message(view=None)
        self.stop()

    async def interaction_check(self, interaction:discord.Interaction) -> bool:
        return interaction.user != self.target_user


# class StageButton(ui.Button):
#     def __init__(self, stage_object:Stage, row:int=0):
#         self.stage:Stage = stage_object
#         super().__init__(label=self.stage.display_name, row=row, style=self.get_style(), disabled=self.get_disabled())
    
#     def get_style(self) -> discord.ButtonStyle:
#         if self.stage.codename in current_state.get_all_striked_stage_codenames():
#             return discord.ButtonStyle.red
#         else:
#             return discord.ButtonStyle.gray
    
#     def get_disabled(self) -> bool:
#         if self.stage.codename in current_state.get_confirmed_striked_stage_codenames():
#             return True
#         if self.stage.codename in current_state.get_pending_striked_stage_codenames():
#             return False
#         return not current_state.can_strike(current_ruleset)
        
#     async def callback(self, interaction:discord.Interaction) -> None:
#         TSHCommunicator.post_click_stage(self.stage)
#         self.view.update_buttons()
#         await interaction.response.edit_message(view=self.view)

# class ConfirmView(ui.View):
#     def __init__(self):
#         super().__init__()
#         self.value = None

#         from math import floor
#         for i in range(len(current_ruleset.neutralStages)):
#             self.add_item(StageButton(current_ruleset.neutralStages[i], floor(float(i)/5.0)))
        
#         if current_state.currGame != 0:
#             for i in range(len(current_ruleset.counterpickStages)):
#                 self.add_item(StageButton(current_ruleset.counterpickStages[i], floor(float(i + len(current_ruleset.neutralStages))/5.0)))
    
#     def update_buttons(self):
#         for child in self.children:
#             child:discord.Button = child
#             if isinstance(child, StageButton):
#                 child:StageButton = child
#                 child.style = child.get_style()
#                 child.disabled = child.get_disabled()


#     confirm_row:int = min(len(current_ruleset.neutralStages), 4)

#     # When the confirm button is pressed, set the inner value to `True` and
#     # stop the View from listening to more input.
#     @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green, row=confirm_row)
#     async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
#         TSHCommunicator.post_confirm_stage_strike()
#         self.update_buttons()
#         await interaction.response.edit_message(content=current_state.currPlayer.display_name, view=self)
    
#     # This one is similar to the confirmation button except sets the inner value to `False`
#     @discord.ui.button(label='Cancel', style=discord.ButtonStyle.grey, row=confirm_row)
#     async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
#         TSHCommunicator.post_reset_stage_strike()
#         await interaction.response.edit_message(content='Cancelled', view=None)
#         self.value = False
#         self.stop()
    
#     @discord.ui.button(label='Undo', style=discord.ButtonStyle.grey, row=confirm_row)
#     async def undo(self, interaction: discord.Interaction, button: discord.ui.Button):
#         TSHCommunicator.post_stage_strike_undo()
#         self.update_buttons()
#         await interaction.response.edit_message(view=self)