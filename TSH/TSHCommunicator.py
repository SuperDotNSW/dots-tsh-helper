import requests
import config
import os
import json
from colorama import Fore, Style
from TSH.TSHObjects import Stage

_cachepath = os.path.dirname(os.path.realpath(__file__)) + "/.cached_TSH_data.json"
_cached_tsh_data:dict = {}
_tsh_connected:bool = False

#### CACHE ####
try:
    _cached_tsh_data = requests.get(f"{config.get_tsh_url()}/ruleset").json()
    with open(_cachepath, "w") as cache_file:
        cache_file.truncate(0)
        cache_file.write(json.dumps(_cached_tsh_data, indent=2))
    _tsh_connected = True
except Exception as e:
    print(f"\n{Fore.RED}ERROR: Couldnt establish connection with TSH at {config.get_tsh_url()} ({e}), using cached TSH data...{Style.RESET_ALL}")

if not os.path.exists(_cachepath):
    print(f"\n{Fore.RED}ERROR: There is no cached TSH data at {_cachepath}! Aborting...")
    quit()
with open(_cachepath) as cache_file:
    _cached_tsh_data = json.loads(cache_file.read())

def fetch_data() -> dict:
    global _cached_tsh_data, _tsh_connected

    data:dict = {}
    if _tsh_connected:
        try:
            return requests.get(f"{config.get_tsh_url()}/ruleset").json()
        except Exception as e:
            print(f"\n{Fore.RED}ERROR: Couldnt establish connection with TSH at {config.get_tsh_url()} ({e}), using cached TSH data...{Style.RESET_ALL}")
            _tsh_connected = False
            return _cached_tsh_data
    else:
        return _cached_tsh_data

def post_confirm_stage_strike():
    requests.post(f"{config.get_tsh_url()}/stage_strike_confirm_clicked")
def post_reset_stage_strike():
    requests.post(f"{config.get_tsh_url()}/stage_strike_reset")
def post_stage_strike_undo():
    requests.post(f"{config.get_tsh_url()}/stage_strike_undo")

def post_stage_strike_match_win(winner:int):
    requests.post(f"{config.get_tsh_url()}/stage_strike_match_win", json={'winner': winner})

def post_rps_win(winner:int):
    requests.post(f"{config.get_tsh_url()}/stage_strike_rps_win", json={'winner': winner})

def post_click_stage(stage_object:Stage):
    requests.post(f"{config.get_tsh_url()}/stage_strike_stage_clicked", json=stage_object.as_dict())