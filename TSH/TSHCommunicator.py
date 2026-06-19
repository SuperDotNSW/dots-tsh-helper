import requests
from TSH.TSHObjects import Stage

BASE_URL = "http://localhost:5000"
TSH_BASE_DIR = ""

current_TSH_data:dict = {}

def fetch_data() -> dict:
    current_TSH_data = requests.get(f"{BASE_URL}/ruleset").json()
    TSH_BASE_DIR = current_TSH_data['basedir']
    return current_TSH_data

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