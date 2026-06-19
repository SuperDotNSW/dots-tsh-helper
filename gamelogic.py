from TSH import TSHCommunicator
from TSH.TSHObjects import Ruleset, State, Stage

from random import randint

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
