from typing import Optional

class Ruleset():
    banByMaxGames:dict = {}
    banCount:int = 3
    counterpickStages:list = []
    neutralStages:list = []
    errors = []
    name:str = ""
    strikeOrder:dict = { 
        0: 1, 
        1: 2, 
        2: 1
    }
    useDSR:bool = False
    useMDSR:bool = True
    videogame:str = ""
    
    def update_from_tsh_data(self, data:dict):
        d = data['ruleset']
        self.banByMaxGames = d['banByMaxGames']
        self.banCount = d['banCount']
        self.counterpickStages = d['counterpickStages']
        self.errors = d['errors']
        self.name = d['name']
        self.neutralStages = d['neutralStages']
        self.strikeOrder = d['strikeOrder']
        self.useDSR = d['useDSR']
        self.useMDSR = d['useMDSR']
        self.videogame = d['videogame']
    
    def __init__(self, tsh_data:Optional[dict]=None):
        if tsh_data is not None:
            self.update_from_tsh_data(tsh_data)

class Player():
    r"""Represents a player participating in a bracket match"""

    # The Name that is displayed in messages referring to this player
    display_name:str = ""
    # The Discord user ID associated with the Player object
    discord_user_id:int = 0

    def __init__(self, display_name:str="", discord_user_id:int=0):
        self.display_name = display_name
        self.discord_user_id = discord_user_id

class State():
    # From the 'state' object retrieved from /ruleset

    canRedo:bool = False
    canUndo:bool = True
    currGame:int = 0
    currPlayer:int = 0
    currStep:int = 0
    gentlemans:bool = False
    lastWinner:int = 0
    selectedStage:dict = {}
    stagesPicked:list = []
    stagesWon:dict = {}
    strikedBy:dict = {}
    strikedStages:dict = {}
    
    p1:Player = Player()
    p2:Player = Player()

    def update_from_tsh_data(self, data:dict):
        d = data['state']
        self.canRedo = d['canRedo']
        self.canUndo = d['canUndo']
        self.currGame = d['currGame']
        self.currPlayer = d['currPlayer']
        self.currStep = d['currStep']
        self.gentlemans = d['gentlemans']
        self.lastWinner = d['lastWinner']
        self.selectedStage = d['selectedStage']
        self.stagesPicked = d['stagesPicked']
        self.stagesWon = d['stagesWon']
        self.strikedBy = d['strikedBy']
        self.strikedStages = d['strikedStages']

        self.p1.display_name = data['p1']
        self.p2.display_name = data['p2']
    
    def __init__(self, tsh_data:Optional[dict]=None):
        if tsh_data is not None:
            self.update_from_tsh_data(tsh_data)