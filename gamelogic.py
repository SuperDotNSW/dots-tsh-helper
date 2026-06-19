from TSH import TSHCommunicator
from TSH.TSHObjects import Ruleset, State, Stage

from discord import File
from random import randint
from os import path

current_ruleset = Ruleset(tsh_data=TSHCommunicator.fetch_data())

class GameInstance():
    """
    If instance ID is set to 0 then banning will be tied directly to the currently active TSH match
    """
    def __init__(self, ID:int, state:State, best_of:int = 3):
        self.ID:int = ID
        self.state:State = state
        assert best_of % 2 == 1
        self.state.best_of = best_of

def stage_to_file(stage:Stage) -> File:
    return File(fp=TSHCommunicator.SHARE.base_dir+stage.icon_path.removeprefix("."), filename=path.basename(stage.icon_path))
