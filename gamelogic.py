from TSH.TSHObjects import Ruleset, State, Stage, Player
from TSH import TSHCommunicator
import discord
from discord import File
from random import randint
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
        self.instinf = views.InstanceInfo(ID, state)
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
    
    def get_available_stages(self) -> list[Stage]:
        # TODO: Account for DSR/MDSR

        # Eliminate stages that have already been banned
        all_striked_stages = self.state.get_all_striked_stages()
        result:list[Stage] = [stage for stage in current_ruleset.neutralStages if not (stage in all_striked_stages)]

        return result
    
    # Instance gets terminated when this function ends
    async def run_match(self):
        # Do RPS for first ban
        self.state.currPlayer = self.state.players[randint(0, 1)]
        self.state.currStep = 0
        self.state.currGame = 0

        # Send RPS feedback
        embed:discord.Embed = views.BaseEmbed(self.instinf)
        embed.title = "RPS Winner"
        embed.description = f"<@{self.state.currPlayer.discord_user.id}> Will strike first."
        embed.colour = discord.Colour.random()
        await self.thread.send(embed=embed)

        # Take turns banning based on strikeOrder
        for step in range(len(current_ruleset.strikeOrder)):
            # Create stage select ui
            stage_ui:FileEmbedContainer = create_stage_embeds(self, self.state)
            # Find remaining pool of stages
            available_stages = self.get_available_stages()
            # Create banning input
            # Only starter stages for first round, uses strikeOrder
            view:views.StageBanningInput = views.StageBanningInput(
                ban_count=current_ruleset.strikeOrder[self.state.currStep],
                available_stages=available_stages,
                target_user=self.state.currPlayer.discord_user
            )
            
            # Send messsage
            if self.current_message:
                await self.current_message.edit(embeds=stage_ui.embeds, view=view)
            else:
                self.current_message = await self.thread.send(embeds=stage_ui.embeds, files=stage_ui.files, view=view)
            
            # Wait for input
            await view.wait()

            if view.values is None:
                # Something went wrong (timeout most likely)
                await _send_error_message()
                return
            else:
                # Ban Stage(s)
                print(f"MATCH #{self.ID}: {view.target_user.display_name} requested ban: {view.values}")
                for codename in view.values:
                    stage:Stage = current_ruleset.find_stage_by_codename(codename)
                    self.state.strikedStages[self.state.currStep].append(stage)
                    self.state.strikedBy[self.state.currPlayer].append(stage)
                
                # Increment step
                self.state.currStep += 1
                self.state.currPlayer = self.state.players[(self.state.get_currplayer_index() + 1) % len(self.state.players)]
                self.state.strikedStages.append([])
        
        print(f"MATCH #{self.ID}: CHOSEN STARTER STAGE: {self.get_available_stages()[0].display_name}")
        report_winner_view:views.ReportWinnerInput = views.ReportWinnerInput(instance_info=self.instinf)
        selected_stage_embed:views.SelectedStageEmbed = views.SelectedStageEmbed(instance_info=self.instinf, stage=self.get_available_stages()[0])
        await self.current_message.edit(embed=selected_stage_embed, attachments=[selected_stage_embed.file], view=report_winner_view)

        await report_winner_view.wait()

        # TODO: Display winner of round in message, then send a new message for the next banning phase
        # TODO: Create embed to show player who won + stage the match took place on
        winner = self.state.players[report_winner_view.value]
        print(f"MATCH #{self.ID}: REPORTED GAME 1 WINNER: {winner.display_name}")
        selected_stage_embed.set_thumbnail(url=winner.discord_user.avatar.url)
        selected_stage_embed.add_field(name="Won by:", value=winner.discord_user.mention)
        await self.current_message.edit(embed=selected_stage_embed)
        return

        for game in range(1, self.state.best_of):
            # TODO: Loop through rounds until winner
            print(f"MATCH #{self.ID}: GAME {game+1} START")
            self.state.currGame = game

            # Check for winner
            for player_id in range(len(self.state.players)):
                if self.state.get_games_won(player_id) >= self.state.games_to_win:
                    # Player has won
                    # TODO: Display all stages played on and final scores
                    print(f"MATCH #{self.ID}: {self.state.players[player].display_name} Has won the set!")
                    return

class FileEmbedContainer:
    def __init__(self):
        self.embeds:list[discord.Embed] = []
        self.files:list[File] = []
def create_stage_embeds(instance:GameInstance, state:State) -> FileEmbedContainer:
    # Lists through all active stages and creates embeds & files for them
    def _create_embeds(stages:list[Stage], neutral:bool=True) -> FileEmbedContainer:
        r = FileEmbedContainer()
        for stage in stages:
            file:File = views.stage_to_file(stage)
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

    # Add player indicator
    player_embed:views.BaseEmbed = views.BaseEmbed(instance.instinf)
    player_embed.title = f"{state.currPlayer.display_name} is banning"
    player_embed.set_thumbnail(url=state.currPlayer.discord_user.display_avatar.url)

    result.embeds.append(player_embed)

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