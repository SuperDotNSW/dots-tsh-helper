import requests
from TSH.TSHObjects import Stage

class Share():
    base_dir:str = ""
    current_data:dict = {}

BASE_URL:str = "http://localhost:5000"
SHARE:Share = Share()

def fetch_data() -> dict:
    SHARE.current_data = requests.get(f"{BASE_URL}/ruleset").json()
    SHARE.base_dir = SHARE.current_data['basedir']
    return SHARE.current_data

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

def post_click_stage(stage_object:Stage):
    requests.post(f"{BASE_URL}/stage_strike_stage_clicked", json=stage_object.as_dict())
    fetch_data()