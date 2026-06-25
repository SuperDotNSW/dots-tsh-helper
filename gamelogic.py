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
        # Eliminate stages that have already been banned
        all_striked_stages = self.state.get_all_striked_stages()
        result:list[Stage] = [stage for stage in current_ruleset.neutralStages if not (stage in all_striked_stages)]
        if self.state.currGame > 0:
            dsr_stages = self.state.get_dsr_stages(current_ruleset.useMDSR)
            # Add counterpick stages
            result.append([stage for stage in current_ruleset.counterpickStages if not (stage in all_striked_stages)])
            # Remove stages that have been DSR'd
            result = [stage for stage in result if not (stage in dsr_stages)]

        return result
    
    def create_banning_input(self, ban_count:int) -> views.StageBanningInput:
        # Create stage select ui
        
        # Find remaining pool of stages
        available_stages = self.get_available_stages()
        # Create banning input
        return views.StageBanningInput(
            ban_count=ban_count,
            available_stages=available_stages,
            target_user=self.state.currPlayer.discord_user
        )

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
            stage_embeds:FileEmbedContainer = create_stage_embeds(self, self.state)
            view:views.StageBanningInput = self.create_banning_input(current_ruleset.strikeOrder[self.state.currStep])
            
            # Send messsage
            if self.current_message:
                await self.current_message.edit(embeds=stage_embeds.embeds, view=view)
            else:
                self.current_message = await self.thread.send(embeds=stage_embeds.embeds, files=stage_embeds.files, view=view)
            
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
        
        # One remaining available stage, stage has been chosen
        chosen_stage:Stage = self.get_available_stages()[0]

        print(f"MATCH #{self.ID}: CHOSEN STARTER STAGE: {chosen_stage.display_name}")
        # Display selected stage in original message and add winner report view
        report_winner_view:views.ReportWinnerInput = views.ReportWinnerInput(instance_info=self.instinf)
        selected_stage_embed:views.SelectedStageEmbed = views.SelectedStageEmbed(instance_info=self.instinf, stage=chosen_stage)
        await self.current_message.edit(embed=selected_stage_embed, attachments=[selected_stage_embed.file], view=report_winner_view)

        await report_winner_view.wait()

        winner = self.state.players[report_winner_view.value]
        print(f"MATCH #{self.ID}: REPORTED GAME 1 WINNER: {winner.display_name}")

        # Update State
        self.state.lastWinner = winner
        self.state.stagesWon[winner].append(chosen_stage)
        self.state.stagesPicked.append(chosen_stage)
        
        # Update Embed
        selected_stage_embed.set_thumbnail(url=winner.discord_user.avatar.url)
        selected_stage_embed.add_field(name="Won by:", value=winner.discord_user.mention)
        await self.current_message.edit(embed=selected_stage_embed)

        self.current_message = None

        for game in range(1, self.state.best_of):
            # Check for winner
            for player_id in range(len(self.state.players)):
                if self.state.get_games_won(player_id) >= self.state.get_games_to_win():
                    # Player has won
                    # TODO: Display all stages played on and final scores
                    print(f"MATCH #{self.ID}: {self.state.players[player].display_name} Has won the set!")
                    return
            
            # TODO: Loop through rounds until winner
            print(f"MATCH #{self.ID}: GAME {game+1} START")
            # Announce current standings
            await self.thread.send(embed=views.GameCountEmbed(self.instinf, self.state))
            # Update current game
            self.state.currGame = game

            ### Do winner bans (UNTESTED) ###
            self.state.currPlayer = self.state.lastWinner

            # Reset striked stages
            self.state.reset_strikes()

            # Update stage_embeds
            stage_embeds:FileEmbedContainer = create_stage_embeds(self, self.state)
            # Create banning view
            view = self.create_banning_input(current_ruleset.banCount)

            self.current_message = await self.thread.send(embeds=stage_embeds.embeds, files=stage_embeds.files, view=view)

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
            ### TODO: Do opponent counterpick ###

            ### Repeat ###

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
            
            # Pending striked stages, should be irrelevant for this bot but just to be thorough
            for s in state.get_pending_striked_stages():
                if s == stage:
                    colour = discord.Colour.dark_red()
            # Striked by player
            for s in state.get_confirmed_striked_stages():
                if s == stage:
                    name = f"~~{name}~~ (Banned)"
                    colour = discord.Colour.red()
            # DSR
            if (current_ruleset.useDSR or current_ruleset.useMDSR):
                if stage in state.get_dsr_stages(current_ruleset.useMDSR):
                    name = f"~~{name}~~ (DSR)"
                    colour = discord.Colour.dark_red()

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
        # Neutral Stages only
        container:FileEmbedContainer = _create_embeds(current_ruleset.neutralStages, True)
        result.embeds += container.embeds
        result.files += container.files
    else:
        # All Stages
        container:FileEmbedContainer = _create_embeds(current_ruleset.neutralStages, True)
        result.embeds += container.embeds
        result.files += container.files
        container = _create_embeds(current_ruleset.counterpickStages, False)
        result.embeds += container.embeds
        result.files += container.files

    return result