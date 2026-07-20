from dotenv import load_dotenv
from os import getenv
from colorama import Fore, Style
import requests
import json
import os

load_dotenv()

# Once again should've made this a class but didn't because i wasnt thinking
# Rewriting it as a class is a chore i dont want to bother with

_scriptdir = os.path.dirname(os.path.realpath(__file__))
_rulesetpath = _scriptdir + "/ruleset.json"
_configpath = _scriptdir + "/config.json"

_configuration:dict = {}
_standard_settings:dict = {}
_obs_settings:dict = {}
_scene_names:dict = {}
_source_names:dict = {}

# Init config

def _read_config_file():
    global _configuration
    # I SHOULD NOT NEED TO FUCKING DO THIS WHY DOES IT THROW AN EXCEPTION IF THERE IS ALREADY A FUCKING FILE
    if os.path.exists(_configpath):
        _configfile = open(_configpath, "r")
    else:
        _configfile = open(_configfile, "x")
    try:
        _configuration = json.loads(_configfile.read())
    except Exception as e:
        print(e)
        _configuration = {}
    _configfile.close()

_read_config_file()

def _write_config_file():
    global _configuration, _standard_settings, _obs_settings, _scene_names, _source_names

    configfile = open(_configpath, "w")
    configfile.truncate(0)

    #### READ FROM EXISTING CONFIGURATION ####
    if not "Standard Settings" in _configuration.keys():
        _configuration["Standard Settings"] = {}
    _standard_settings = _configuration["Standard Settings"]

    if not "OBS Settings" in _configuration.keys():
        _configuration["OBS Settings"] = {}
    _obs_settings = _configuration["OBS Settings"]

    if not "Scene Names" in _obs_settings.keys():
        _configuration["OBS Settings"]["Scene Names"] = {}
    _scene_names = _configuration["OBS Settings"]["Scene Names"]
    if not "Source Names" in _obs_settings.keys():
        _configuration["OBS Settings"]["Source Names"] = {}
    _source_names = _configuration["OBS Settings"]["Source Names"]
    
    ##### DEFINE DEFAULTS #####
    if not "max_best_of" in _standard_settings.keys():
        _standard_settings["max_best_of"] = 9
    if not "duel_request_timeout" in _standard_settings.keys():
        _standard_settings["duel_request_timeout"] = 120.0
    if not "delete_expired_requests" in _standard_settings.keys():
        _standard_settings["delete_expired_requests"] = False
    if not "tsh_target_url" in _standard_settings.keys():
        _standard_settings["tsh_target_url"] = "http://localhost:5000"
    if not "match_admins" in _standard_settings.keys():
        _standard_settings["match_admins"] = [
            255974807944822784
        ]
    
    if not "enabled" in _obs_settings.keys():
        _configuration["OBS Settings"]["enabled"] = False
    if not "websocket_port" in _obs_settings.keys():
        _configuration["OBS Settings"]["websocket_port"] = 4433
    
    if not "versus_scene" in _scene_names.keys():
        _scene_names["versus_scene"] = "Versus"
    if not "game_scene" in _scene_names.keys():
        _scene_names["game_scene"] = "Game"
    if not "versus_song" in _source_names.keys():
        _source_names["versus_song"] = "VersusSong"
    if not "finale_song" in _source_names.keys():
        _source_names["finale_song"] = "FinaleSong"
    if not "results_song" in _source_names.keys():
        _source_names["results_song"] = "ResultsSong"
    if not "striking_overlay" in _source_names.keys():
        _source_names["striking_overlay"] = "striking.html"
    
    _obs_settings["Scene Names"] = _scene_names
    _obs_settings["Source Names"] = _source_names
    
    _configuration = {
        "Standard Settings" : _standard_settings,
        "OBS Settings" : _obs_settings
    }

    print(f"Wrote to {_configpath}")
    configfile.write(json.dumps(_configuration, indent=2))
    configfile.close()

_write_config_file()

# FUNCTION IMPLEMENTATIONS
def get_max_best_of() -> int:
    _read_config_file()
    return _standard_settings["max_best_of"]

def get_match_request_timeout() -> float:
    _read_config_file()
    return _standard_settings["duel_request_timeout"]

def get_delete_expired_requests() -> bool:
    _read_config_file()
    return _standard_settings["delete_expired_requests"]
def get_tsh_url() -> str:
    _read_config_file()
    return _standard_settings["tsh_target_url"]

def get_obs_enabled() -> bool:
    _read_config_file()
    return _obs_settings["enabled"]
def get_obs_port() -> int:
    _read_config_file()
    return _obs_settings["websocket_port"]
def get_obs_password() -> str:
    _read_config_file()
    return getenv("OBS_PASS")
def get_versus_scene_name() -> str:
    _read_config_file()
    return _scene_names["versus_scene"]
def get_game_scene_name() -> str:
    _read_config_file()
    return _scene_names["game_scene"]
def get_versus_song_name() -> str:
    _read_config_file()
    return _source_names["versus_song"]
def get_finale_song_name() -> str:
    _read_config_file()
    return _source_names["finale_song"]
def get_results_song_name() -> str:
    _read_config_file()
    return _source_names["results_song"]
def get_striking_name() -> str:
    _read_config_file()
    return _source_names["striking_overlay"]
def is_user_id_admin(user_id:int) -> bool:
    _read_config_file()
    return user_id in _standard_settings["match_admins"]

