from typing import Optional
from math import ceil

class Stage():
    """
    Represents a stage with a codename, display name and icon path\n
    Can also be serialized to a dict for communicating with TSH
    """

    def __init__(self, stage_data:dict):
        self.codename:str = stage_data['codename']
        self.display_name:str = stage_data['display_name']
        self.icon_path:str = stage_data['path']
    
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

    def __init__(self, tsh_data:Optional[dict]=None):
        self.banByMaxGames:dict = {}
        self.banCount:int = 3
        self.counterpickStages:list = []
        self.neutralStages:list = []
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
            self.update_from_tsh_data(tsh_data)

    def update_from_tsh_data(self, data:dict):
        d = data['ruleset']
        self.banByMaxGames = d['banByMaxGames']
        self.banCount = d['banCount']
        self.errors = d['errors']
        self.name = d['name']
        self.strikeOrder = d['strikeOrder']
        self.useDSR = d['useDSR']
        self.useMDSR = d['useMDSR']
        self.videogame = d['videogame']

        self.neutralStages:list[Stage]
        self.counterpickStages:list[Stage]
        self.neutralStages.clear()
        self.counterpickStages.clear()
        for stagedata in d['neutralStages']:
            self.neutralStages.append(Stage(stagedata))
        for stagedata in d['counterpickStages']:
            self.counterpickStages.append(Stage(stagedata))
    
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

    def __init__(self, display_name:str="", discord_user_id:int=0):
        # The Name that is displayed in messages referring to this player
        self.display_name = display_name
        # The Discord user ID associated with the Player object
        self.discord_user_id = discord_user_id

class State():
    """
    Contains all state information of the current match.
    """
    # From the 'state' object retrieved from /ruleset
    def __init__(self, best_of:int = 3, tsh_data:Optional[dict]=None):
        self.canRedo:bool = False
        self.canUndo:bool = True
        self.currGame:int = 0
        self.currPlayer:int = 0
        self.currStep:int = 0
        self.gentlemans:bool = False
        self.lastWinner:int = 0
        self.selectedStage:dict = {}
        self.stagesPicked:list = []
        self.stagesWon:dict = {}
        self.strikedBy:dict = {}
        self.strikedStages:list[str]
        self.best_of = best_of
        
        self.p1:Player = Player()
        self.p2:Player = Player()

        if tsh_data is not None:
            self.best_of = tsh_data['best_of']
            self.update_from_tsh_data(tsh_data)
    
    def update_from_tsh_data(self, data:dict):
        d = data['state']
        self.canRedo = d['canRedo']
        self.canUndo = d['canUndo']
        self.currGame:int = d['currGame']
        if d['currPlayer'] == 0:
            self.currPlayer = self.p1
        else:
            self.currPlayer = self.p2
        self.currStep:int = d['currStep']
        self.gentlemans:bool = d['gentlemans']
        self.lastWinner:int = d['lastWinner']
        self.selectedStage:str = d['selectedStage']
        self.stagesPicked:list[str] = d['stagesPicked']
        self.stagesWon:list = d['stagesWon']
        self.strikedBy:list = d['strikedBy']
        self.strikedStages:list = d['strikedStages']

        self.p1.display_name = data['p1']
        self.p2.display_name = data['p2']
    
    @property
    def games_to_win(self) -> int:
        return ceil(float(self.best_of) / 2.0)

    def get_all_striked_stage_codenames(self) -> list[str]:
        stages:list[str] = []
        for step in self.strikedStages:
            for stage in step:
                stages.append(stage)
        
        return stages
    
    def get_confirmed_striked_stage_codenames(self) -> list[str]:
        stages:list[str] = []
        for i in range(len(self.strikedStages)):
            if i >= self.currStep:
                continue
            for stage in self.strikedStages[i]:
                stages.append(stage)
        
        return stages

    def get_pending_striked_stage_codenames(self) -> list[str]:
        return self.strikedStages[self.currStep]
    
    def can_strike(self, ruleset:Ruleset) -> bool:
        stages_to_strike:int = 0
        if self.currGame == 0:
            if self.currStep == len(ruleset.strikeOrder):
                return False
            return ruleset.strikeOrder[self.currStep] > len(self.get_pending_striked_stage_codenames())

        if ruleset.best_of == 0:
            return True

        if ruleset.banCount == 0:
            return ruleset.banByMaxGames[ruleset.best_of] > len(self.get_pending_striked_stage_codenames())
        else:
            return ruleset.banCount > len(self.get_pending_striked_stage_codenames())