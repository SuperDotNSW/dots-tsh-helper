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
    
    async def _send_error_message(self):
        embed = discord.Embed(
            colour=discord.Colour.red(),
            title="ERROR: Match cannot continue",
            timestamp=datetime.datetime.now(datetime.UTC),
            description="An unknown error has occured and the match has been terminated."
        )
        embed.set_footer(f"#{self.ID}")
        await self.current_message.reply(embed=embed)
    
    async def run_match(self):
        # Do RPS for first ban
        self.state.currPlayer = randint(0, 1)
        self.state.currStep = 0
        self.state.currGame = 0

        # Send RPS feedback
        embed:discord.Embed = BaseEmbed(self.ID)
        embed.title = "RPS Winner"
        embed.description = f"<@{self.state.get_current_player().discord_user.id}> Will strike first."
        embed.colour = discord.Colour.random()
        await self.thread.send(embed=embed)

        # Take turns banning based on strikeOrder
        for step in range(len(current_ruleset.strikeOrder)):
            # Create stage select ui
            stage_ui:FileEmbedContainer = create_stage_embeds(self.state)
            # Find remaining pool of stages
            all_striked_stages = self.state.get_all_striked_stages()
            available_stages = [stage for stage in current_ruleset.neutralStages if stage not in all_striked_stages]
            # Create banning input
            # Only starter stages for first round, uses strikeOrder
            view:views.StageBanningInput = views.StageBanningInput(
                ban_count=current_ruleset.strikeOrder[self.state.currStep],
                available_stages=available_stages,
                target_user=self.state.get_current_player()
            )

            # Send messsage
            if self.current_message:
                await self.current_message.edit(embeds=stage_ui.embeds, view=view)
            else:
                self.current_message = await self.thread.send(embeds=stage_ui.embeds, files=stage_ui.files, view=view)
            
            await view.wait()
            if view.values is None:
                # Something went wrong (timeout most likely)
                await _send_error_message()
                return
            else:
                # Ban Stage(s)
                for codename in view.values:
                    stage:Stage = current_ruleset.find_stage_by_codename(codename)
                    self.state.strikedStages[self.state.currStep].append(stage)
                    self.state.strikedBy[self.state.currPlayer].append(stage)
                
                # Increment step
                self.state.currStep += 1
                self.state.strikedStages.append([])

        for game in range(1, self.state.best_of):
            # Loop through rounds until winner
            print(f"MATCH #{self.ID}: GAME {game} START")
            self.state.currGame = game

            # Check for winner
            for player_id in range(len(self.state.players)):
                if self.state.get_games_won(player_id) >= self.state.games_to_win:
                    # Player has won
                    print(f"{self.state.players[player].display_name} Has won the set! (Match #{self.ID})")
                    return

def stage_to_file(stage:Stage) -> File:
    return File(fp=TSHCommunicator.SHARE.base_dir+stage.icon_path.removeprefix("."), filename=path.basename(stage.icon_path))

class BaseEmbed(discord.Embed):
    """
    Creates an embed that has timestamp and game ID in the footer by default
    """
    def __init__(self, instID:int):
        super().__init__(timestamp=datetime.datetime.now(datetime.UTC))
        self.set_footer(text=f"#{instID}")

class FileEmbedContainer:
    def __init__(self):
        self.embeds:list[discord.Embed] = []
        self.files:list[File] = []
def create_stage_embeds(state:State) -> FileEmbedContainer:

    def _create_embeds(stages:list[Stage], neutral:bool=True) -> FileEmbedContainer:
        r = FileEmbedContainer()
        for stage in stages:
            file:File = stage_to_file(stage)
            name:str = stage.display_name
            colour:discord.Colour = discord.Colour.light_grey()
            description:str
            if neutral:
                description = "Neutral Stage"
            else:
                description = "Counterpick Stage"

            for s in state.get_pending_striked_stages():
                if s == stage:
                    colour = discord.Colour.dark_red()
            for s in state.get_confirmed_striked_stages():
                if s == stage:
                    name = f"~~{name}~~ (Banned)"
                    colour = discord.Colour.red()

            embed:discord.Embed = discord.Embed(colour=colour, title=name, description=description)
            embed.set_thumbnail(url=file.uri)
            r.embeds.append(embed)
            r.files.append(file)
        return r
    
    result = FileEmbedContainer()

    if state.currGame == 0:
        # Game 1
        container:FileEmbedContainer = _create_embeds(current_ruleset.neutralStages, True)
        result.embeds += container.embeds
        result.files += container.files
    else:
        # Beyond
        container:FileEmbedContainer = _create_embeds(current_ruleset.neutralStages, True)
        result.embeds += container.embeds
        result.files += container.files
        container = _create_embeds(current_ruleset.counterpickStages, False)
        result.embeds += container.embeds
        result.files += container.files

    return result