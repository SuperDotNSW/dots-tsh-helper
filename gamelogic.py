from TSH import TSHCommunicator
from TSH.TSHObjects import Ruleset, State, Stage, Player

import discord
from discord import File
from random import randint
from os import path
import datetime
import views

current_ruleset = Ruleset(tsh_data=TSHCommunicator.fetch_data())

class GameInstance():
    """
    If instance ID is set to 0 then banning will be tied directly to the currently active TSH match
    """
    def __init__(self, ID:int, thread:discord.Thread, state:State):
        self.ID:int = ID
        self.state:State = state
        self.thread = thread
        self.active = True
        self.current_message:discord.Message = None
    
    def _get_current_player(self) -> Player:
        return self.state.players[self.state.currPlayer]

    async def run_match(self):
        # Do RPS for first ban
        self.state.currPlayer = randint(0, 1)
        self.state.currStep = 0
        self.state.currGame = 0

        # Send RPS feedback
        embed:discord.Embed = BaseEmbed(self.ID)
        embed.title = "RPS Winner"
        embed.description = f"<@{self._get_current_player().discord_user.id}> Will strike first."
        embed.colour = discord.Colour.random()
        await self.thread.send(embed=embed)

        for game in range(self.state.best_of):
            print(f"MATCH #{self.ID}: GAME {game} START")
            self.state.currGame = game
            for player_id in range(len(self.state.players)):
                if self.state.get_games_won(player_id) >= self.state.games_to_win:
                    # Player has won
                    print(f"{self.state.players[player].display_name} Has won the set! (Match #{self.ID})")
                    return
            
            # Create stage select ui
            stage_ui:StageSelectContainer = create_stage_embeds(self.state)
            # Create banning input
            view:views.StageBanningInput = views.StageBanningInput(
                ban_count=current_ruleset.strikeOrder[self.state.currStep],
                available_stages=current_ruleset.neutralStages, 
                target_user=self._get_current_player()
            )
            # Send messsage
            self.current_message = await self.thread.send(embeds=stage_ui.embeds, files=stage_ui.files, view=view)
            await view.wait()
            print(view.value)
            if view.value is None:
                # Something went wrong (timeout most likely)
                pass
            else:
                # Ban Stage(s)
                pass

class BaseEmbed(discord.Embed):
    """
    Creates an embed that has timestamp and game ID in the footer by default
    """
    def __init__(self, instID:int):
        super().__init__(timestamp=datetime.datetime.now(datetime.UTC))
        self.set_footer(text=f"#{instID}")

class StageSelectContainer:
    def __init__(self):
        self.embeds:list[discord.Embed] = []
        self.files:list[File] = []
def create_stage_embeds(state:State) -> StageSelectContainer:
    result = StageSelectContainer()

    def _create_embeds(stages:list[Stage], neutral:bool=True) -> StageSelectContainer:
        r = StageSelectContainer()
        for stage in stages:
            file:File = stage_to_file(stage)
            name:str = stage.display_name
            colour:discord.Colour = discord.Colour.light_grey()
            description:str
            if neutral:
                description = "Neutral Stage"
            else:
                description = "Counterpick Stage"

            for codename in state.get_pending_striked_stage_codenames():
                if current_ruleset.find_stage_by_codename(codename) == stage:
                    colour = discord.Colour.dark_red()
            for codename in state.get_confirmed_striked_stage_codenames():
                if current_ruleset.find_stage_by_codename(codename) == stage:
                    name = f"~~{name}~~ (Banned)"
                    colour = discord.Colour.red()

            embed:discord.Embed = discord.Embed(colour=colour, title=name, description=description)
            embed.set_thumbnail(url=file.uri)
            r.embeds.append(embed)
            r.files.append(file)
        return r

    if state.currGame == 0:
        # Game 1
        container:StageSelectContainer = _create_embeds(current_ruleset.neutralStages, True)
        result.embeds += container.embeds
        result.files += container.files
    else:
        # Beyond
        container:StageSelectContainer = _create_embeds(current_ruleset.neutralStages, True)
        result.embeds += container.embeds
        result.files += container.files
        container = _create_embeds(current_ruleset.counterpickStages, False)
        result.embeds += container.embeds
        result.files += container.files

    return result

def stage_to_file(stage:Stage) -> File:
    return File(fp=TSHCommunicator.SHARE.base_dir+stage.icon_path.removeprefix("."), filename=path.basename(stage.icon_path))
