import requests
from TSHObjects import State, Ruleset, Player, Stage

BASE_URL = "http://localhost:5000"

current_state = State()
current_ruleset = Ruleset()

def fetch_data() -> dict:
    data = requests.get(f"{BASE_URL}/ruleset").json()
    current_state.update_from_tsh_data(data)
    current_ruleset.update_from_tsh_data(data)
    return data

def post_confirm_stage_strike():
    requests.post(f"{BASE_URL}/stage_strike_confirm_clicked")
    fetch_data()
def post_reset_stage_strike():
    requests.post(f"{BASE_URL}/stage_strike_reset")
    fetch_data()
def post_stage_strike_undo():
    requests.post(f"{BASE_URL}/stage_strike_undo")
    fetch_data()

def post_rps_win(winner:int):
    requests.post(f"{BASE_URL}/stage_strike_rps_win", json={'winner': winner})

def request_strike_stage(stage_object:Stage):
    requests.post(f"{BASE_URL}/stage_strike_stage_clicked", json=stage_object.as_dict())
    fetch_data()