from typing import Optional
from math import ceil
import discord

class Stage():
    """
    Represents a stage with a codename, display name and icon path\n
    Can also be serialized to a dict for communicating with TSH
    """

    def __init__(self, stage_data:dict):
        self.codename:str = stage_data['codename']
        self.display_name:str = stage_data['display_name']
        self.icon_path:str = stage_data['path']
        self.neutral:bool = True
    
    def as_dict(self) -> dict:
        return {
            'codename': self.codename,
            'display_name': self.display_name,
            'icon': self.icon_path
        }


class Ruleset():
    """
    Contains all information related to ruleset, stagelists, etc.\n
    This object should rarely be modified
    """

    def __init__(self, tsh_data:Optional[dict]=None, best_of:Optional[int]=3):
        self.banByMaxGames:dict = {}
        self.banCount:int = 3
        self.counterpickStages:list[Stage] = []
        self.neutralStages:list[Stage] = []
        self.errors = []
        self.name:str = ""
        self.strikeOrder:dict = { 
            0: 1, 
            1: 2, 
            2: 1
        }
        self.useDSR:bool = False
        self.useMDSR:bool = True
        self.videogame:str = ""

        if tsh_data is not None:
            self.update_from_json_data(tsh_data['ruleset'], best_of)

    def update_from_json_data(self, data:dict, best_of:int=3):
        self.banByMaxGames = data['banByMaxGames']
        if self.banByMaxGames != {}:
            print("WARNING: banByMaxGames is broken in the TSH webapp! Please use banCount for streamed matches!")
            
            if self.banByMaxGames.get(best_of):
                self.banCount = self.banByMaxGames[best_of]
            else:
                print(f"ERROR: There is no ban count defined for best of {best_of}.\nUsing fallback value of 3")
                self.banCount = 3
        else:
            self.banCount = data['banCount']
        
        self.errors = data['errors']
        self.name = data['name']
        self.strikeOrder = data['strikeOrder']
        self.useDSR = data['useDSR']
        self.useMDSR = data['useMDSR']
        self.videogame = data['videogame']

        self.neutralStages.clear()
        self.counterpickStages.clear()
        for stagedata in data['neutralStages']:
            self.neutralStages.append(Stage(stagedata))
        for stagedata in data['counterpickStages']:
            newstage:Stage = Stage(stagedata)
            newstage.neutral = False
            self.counterpickStages.append(newstage)
    
    def find_stage_by_codename(self, codename:str) -> Stage:
        for stage in self.neutralStages:
            if codename == stage.codename:
                return stage
        for stage in self.counterpickStages:
            if codename == stage.codename:
                return stage
        
        return None

class Player():
    r"""Represents a player participating in a bracket match"""

    def __init__(self, display_name:str="", discord_user:discord.User=None):
        # The Discord user ID associated with the Player object
        self.discord_user:discord.User = discord_user
        # The Name that is displayed in messages referring to this player
        self._display_name:str = display_name
        if discord_user:
            self._display_name = discord_user.global_name
    
    @property
    def display_name(self) -> str:
        if self._display_name == "" and self.discord_user:
            return self.discord_user.global_name
        else:
            return self._display_name
    
    @display_name.setter
    def display_name(self, value:str):
        self._display_name = value

class State():
    """
    Contains all state information of the current match.
    """
    # From the 'state' object retrieved from /ruleset
    def __init__(self, best_of:int = 3, tsh_data:Optional[dict]=None):
        self.canRedo:bool = False
        self.canUndo:bool = False
        self.currGame:int = 0
        self.currStep:int = -1
        self.gentlemans:bool = False
        self.lastWinner:Player = None
        self.selectedStage:str = None
        self.stagesPicked:list = []
        self.strikedStages:list[[list[Stage]]] = [[]]
        assert best_of % 2 == 1
        self.best_of = best_of
        
        self.p1:Player = Player()
        self.p2:Player = Player()

        self.players:list[Player] = [
            self.p1,
            self.p2
        ]
        self.currPlayer:Player = self.players[0]
        self.stagesWon:dict[Player, list[Stage]] = {
            self.p1 : [],
            self.p2 : []
        }
        self.strikedBy:dict[Player, list[Stage]] = {
            self.p1 : [],
            self.p2 : []
        }

        if tsh_data is not None:
            self.best_of = tsh_data['best_of']
            self.update_from_tsh_data(tsh_data)
    
    def update_from_tsh_data(self, data:dict, ruleset:Ruleset=None):
        self.p1.display_name = data['p1']
        self.p2.display_name = data['p2']

        d = data['state']
        if d != {}:
            self.canRedo = d['canRedo']
            self.canUndo = d['canUndo']
            self.currGame = d['currGame']
            self.currPlayer:Player = self.players[d['currPlayer']]
            self.currStep = d['currStep']
            self.gentlemans = d['gentlemans']
            self.lastWinner = self.players[d['lastWinner']]
        
            # Only retrieve stage information if a ruleset is provided
            if ruleset:
                self.selectedStage = ruleset.find_stage_by_codename(d['selectedStage'])
                self.stagesPicked = []
                for codename in d['stagesPicked']:
                    self.stagesPicked.append(ruleset.find_stage_by_codename(codename))
                
                # Reset stagesWon
                self.stagesWon = {
                    self.p1 : [],
                    self.p2 : []
                }
                # Retrieve from TSH
                for p in range(len(d['stagesWon'])):
                    for codename in d['stagesWon'][p]:
                        self.stagesWon[self.players[p]].append(ruleset.find_stage_by_codename(codename))
                
                # Reset strikedBy
                self.strikedBy = {
                    self.p1 : [],
                    self.p2 : []
                }
                # Retrieve from TSH
                for p in range(len(d['strikedBy'])):
                    for codename in d['strikedBy'][p]:
                        self.strikedBy[self.players[p]].append(ruleset.find_stage_by_codename(codename))
                
                # Reset strikedStages
                self.strikedStages = [[]]
                # Retrieve from TSH
                for step in range(len(d['strikedStages'])):
                    self.strikedStages.append([])
                    for codename in d['strikedStages'][step]:
                        self.strikedStages[step].append(ruleset.find_stage_by_codename(codename))
    
    def get_games_to_win(self) -> int:
        return ceil(float(self.best_of) / 2.0)
    
    def get_currplayer_index(self) -> int:
        return self.players.index(self.currPlayer)

    def get_games_won(self, player:Player) -> int:
        if len(self.stagesWon) == 0:
            return 0
        return len(self.stagesWon[player])

    def get_all_striked_stages(self) -> list[Stage]:
        stages:list[Stage] = []
        for step in self.strikedStages:
            for stage in step:
                stages.append(stage)
        
        return stages
    
    def get_confirmed_striked_stages(self) -> list[Stage]:
        stages:list[Stage] = []
        for i in range(len(self.strikedStages)):
            if i >= self.currStep:
                continue
            for stage in self.strikedStages[i]:
                stages.append(stage)
        
        return stages

    def get_pending_striked_stages(self) -> list[Stage]:
        if len(self.strikedStages) <= self.currStep:
            return []
        return self.strikedStages[self.currStep]
    
    def can_strike(self, ruleset:Ruleset) -> bool:
        stages_to_strike:int = 0
        if self.currGame == 0:
            if self.currStep == len(ruleset.strikeOrder):
                return False
            return ruleset.strikeOrder[self.currStep] > len(self.get_pending_striked_stages())

        if ruleset.best_of == 0:
            return True

        if ruleset.banCount == 0:
            return ruleset.banByMaxGames[ruleset.best_of] > len(self.get_pending_striked_stages())
        else:
            return ruleset.banCount > len(self.get_pending_striked_stages())
    
    def get_dsr_stages(self, use_mdsr=bool) -> list[Stage]:
        result:list[Stage] = []
        player_to_check:Player = None
        if self.currPlayer == self.lastWinner:
            player_to_check = self.players[(self.get_currplayer_index() + 1) % len(self.players)]
        else:
            player_to_check = self.currPlayer
        
        if player_to_check == None:
            return result
        
        if use_mdsr:
            for s in self.stagesWon[player_to_check]:
                result.append(s)
        else:
            for p in self.stagesWon:
                for s in self.stagesWon[p]:
                    result.append(s)
        return result
    
    def reset_strikes(self):
        for p in self.strikedBy:
            self.strikedBy[p] = []
        for step in range(len(self.strikedStages)):
            self.strikedStages[step] = []

