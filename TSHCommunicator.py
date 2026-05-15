import requests
from TSHObjects import State, Ruleset, Player

BASE_URL = "http://localhost:5000"

current_state = State()
current_ruleset = Ruleset()

def fetch_data() -> dict:
    data = requests.get(f"{BASE_URL}/ruleset").json()
    current_state.update_from_tsh_data(data)
    current_ruleset.update_from_tsh_data(data)
    return data

def request_strike_stage(stage_object:dict):
    requests.post(f"{BASE_URL}/stage_strike_stage_clicked", json=stage_object)
    fetch_data()