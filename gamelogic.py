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
        self.banning_msgs:list[discord.Message] = []
    
    async def _send_error_message(self):
        embed = discord.Embed(
            colour=discord.Colour.red(),
            title="ERROR: Match cannot continue",
            timestamp=datetime.datetime.now(datetime.UTC),
            description="An unknown error has occured and the match has been terminated."
        )
        embed.set_footer(text=f"#{self.ID}")
        await self.thread.send(embed=embed)
    
    def get_available_stages(self) -> list[Stage]:
        # Eliminate stages that have already been banned
        all_striked_stages = self.state.get_all_striked_stages()
        result:list[Stage] = [stage for stage in current_ruleset.neutralStages if not (stage in all_striked_stages)]
        if self.state.currGame > 0:
            dsr_stages = self.state.get_dsr_stages(current_ruleset.useMDSR)
            # Add counterpick stages
            for stage in [stage for stage in current_ruleset.counterpickStages if not (stage in all_striked_stages)]:
                result.append(stage)
            # Remove stages that have been DSR'd
            result = [stage for stage in result if not (stage in dsr_stages)]
        
        return result
    
    # Creates a view that allows the user to input their bans in a dropdown
    def create_stage_banning_input(self, ban_count:int) -> views.StageBanningInput:
        # Find remaining pool of stages
        available_stages:list[Stage] = self.get_available_stages()
        # Create banning input
        return views.StageBanningInput(
            ban_count=ban_count,
            available_stages=available_stages,
            target_user=self.state.currPlayer.discord_user
        )
    
    def create_stage_select_input(self) -> views.StageSelectInput:
        # Find remaining pool of stages
        available_stages:list[Stage] = self.get_available_stages()
        # Create banning input
        return views.StageSelectInput(
            available_stages=available_stages,
            target_user=self.state.currPlayer.discord_user
        )
    
    # Creates stage banning input message, waits for user input, then returns the view after recieving bans
    async def send_stage_msg(self, is_picking:bool=False) -> views.StageInputBase:
        stage_embeds:FileEmbedContainer = create_stage_embeds(self, self.state)
        view:views.StageInputBase
        if is_picking:
            view = self.create_stage_select_input()
        else:    
            if self.state.currGame == 0:
                view = self.create_stage_banning_input(current_ruleset.strikeOrder[self.state.currStep])
            else:
                view = self.create_stage_banning_input(current_ruleset.banCount)

        embed_batches:list[[discord.Embed]] = []
        file_batches:list[[File]] = []
        for i in range(0, len(stage_embeds.embeds), 10):
            # Gets the next 10 embeds in stage_embeds and packs them into a list
            # which then gets appended to embed_batches and file_batches
            embed_batches.append([stage_embeds.embeds[emb] for emb in range(i, i + min(len(stage_embeds.embeds)-i, 10))])
            # -1 file to account for the "Currently Banning" embed
            # FIXME: DOESNT WORK FOR FINAL STAGE IN 10 STAGE POOL (1st embed in second message)
            file_batches.append([stage_embeds.files[emb-1] for emb in range(i, i + min(len(stage_embeds.files)-i, 10))])
        
        if len(self.banning_msgs) == 0:
            # Send new messages if banning_msgs is empty
            for i in range(len(embed_batches)):
                embeds:list[discord.Embed] = embed_batches[i]
                files:list[File] = file_batches[i]
                
                if i + 1 == len(embed_batches):
                    # Add view to message if this is the last batch
                    self.banning_msgs.append(await self.thread.send(embeds=embeds, files=files, view=view))
                else:
                    self.banning_msgs.append(await self.thread.send(embeds=embeds, files=files))
        else:
            # Edits existing messages if banning_msgs has existing elements
            for i in range(len(embed_batches)):
                embeds:list[discord.Embed] = embed_batches[i]

                # Dont need to add files as they should already be in the messsages
                if i + 1 == len(embed_batches):
                    # Add view to message if this is the last batch
                    await self.banning_msgs[i].edit(embeds=embeds, view=view)
                else:
                    await self.banning_msgs[i].edit(embeds=embeds)
        
        # Wait for selection
        await view.wait()

        # Return view
        return view
    
    # Creates a message that allows users to report the winner of the match, awaits the input, then returns the resulting player
    async def create_report_winner_view(self, selected_stage_embed:views.SelectedStageEmbed) -> Player:
        # Display selected stage in original message and add winner report view
        report_winner_view:views.ReportWinnerInput = views.ReportWinnerInput(instance_info=self.instinf)
        for i in range(len(self.banning_msgs)):
            if i == 0:
                # Replace first message in list with winner report
                await self.banning_msgs[i].edit(embed=selected_stage_embed, attachments=[selected_stage_embed.file], view=report_winner_view)
            else:
                # Delete all subsequent messages
                await self.banning_msgs[i].delete()
        
        # Wait for players to decide on winner
        await report_winner_view.wait()

        # Return resulting winner
        return self.state.players[report_winner_view.value]

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
            # Send messsage and wait for input
            bans_view = await self.send_stage_msg()

            if bans_view.values is None:
                # Something went wrong (timeout most likely)
                await self._send_error_message()
                return
            else:
                # Ban Stage(s)
                print(f"MATCH #{self.ID}: {bans_view.target_user.display_name} requested ban: {bans_view.values}")
                for codename in bans_view.values:
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

        # This is terrible spaghetti. Oh well!
        selected_stage_embed:views.SelectedStageEmbed = views.SelectedStageEmbed(instance_info=self.instinf, stage=chosen_stage)
        winner = await self.create_report_winner_view(selected_stage_embed)

        print(f"MATCH #{self.ID}: REPORTED GAME 1 WINNER: {winner.display_name}")

        # Update State
        self.state.lastWinner = winner
        self.state.stagesWon[winner].append(chosen_stage)
        self.state.stagesPicked.append(chosen_stage)
        
        # Update Embed
        selected_stage_embed.set_thumbnail(url=winner.discord_user.avatar.url)
        selected_stage_embed.add_field(name="Won by:", value=winner.discord_user.mention)
        await self.banning_msgs[0].edit(embed=selected_stage_embed)

        self.banning_msgs = []

        # End match immediately if bo1
        if self.state.best_of == 1:
            print(f"MATCH #{self.ID}: {winner.display_name} Has won the set!")
            await self.thread.send(embed=views.GameCountEmbed(self.instinf, self.state))
            # End Match~!
            return

        for game in range(1, self.state.best_of):
            # Announce current standings
            await self.thread.send(embed=views.GameCountEmbed(self.instinf, self.state))

            # Check for winner
            for player in self.state.players:
                if self.state.get_games_won(player) >= self.state.get_games_to_win():
                    # Player has won
                    print(f"MATCH #{self.ID}: {player.display_name} Has won the set!")
                    # End Match~!
                    return

            # Update current game
            self.state.currGame = game
            self.state.currStep = 0
            self.state.reset_strikes()
            
            # TODO: Loop through rounds until winner
            print(f"MATCH #{self.ID}: GAME {game+1} START")

            ### Do winner bans ###

            # Create banning view
            self.state.currPlayer = self.state.lastWinner
            bans_view = await self.send_stage_msg()

            if bans_view.values is None:
                # Something went wrong (timeout most likely)
                await self._send_error_message()
                return
            else:
                # Ban Stage(s)
                print(f"MATCH #{self.ID}: {bans_view.target_user.display_name} requested ban: {bans_view.values}")
                for codename in bans_view.values:
                    stage:Stage = current_ruleset.find_stage_by_codename(codename)
                    self.state.strikedStages[self.state.currStep].append(stage)
                    self.state.strikedBy[self.state.currPlayer].append(stage)
                
                # Increment step
                self.state.currStep += 1
                self.state.currPlayer = self.state.players[(self.state.get_currplayer_index() + 1) % len(self.state.players)]
            
            ### Do opponent counterpick ###
            self.state.currPlayer = self.state.lastWinner
            counterpick_view = await self.send_stage_msg(is_picking=True)
            chosen_stage:Stage = None

            if counterpick_view.values is None:
                # Something went wrong (timeout most likely)
                await self._send_error_message()
                return
            else:
                # Pick Stage
                print(f"MATCH #{self.ID}: {counterpick_view.target_user.display_name} requested counterpick: {counterpick_view.values}")
                chosen_stage = current_ruleset.find_stage_by_codename(counterpick_view.values[0])
                self.state.stagesPicked.append(chosen_stage)
                
                # Increment step
                self.state.currStep += 1

            ### Report winner ###

            # This is terrible spaghetti. Oh well!
            selected_stage_embed:views.SelectedStageEmbed = views.SelectedStageEmbed(instance_info=self.instinf, stage=chosen_stage)
            winner = await self.create_report_winner_view(selected_stage_embed)

            print(f"MATCH #{self.ID}: REPORTED GAME {game+1} WINNER: {winner.display_name}")

            # Update State
            self.state.lastWinner = winner
            self.state.stagesWon[winner].append(chosen_stage)

            # Update Embed
            selected_stage_embed.set_thumbnail(url=winner.discord_user.avatar.url)
            selected_stage_embed.add_field(name="Won by:", value=winner.discord_user.mention)
            await self.banning_msgs[0].edit(embed=selected_stage_embed)

            self.banning_msgs = []

            ### Repeat ###
            # await self._send_error_message()
            # return


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