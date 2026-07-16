from dotenv import load_dotenv
from os import getenv

load_dotenv()

# TODO: Convert this to .json file that can be reloaded during execution
# im so lazy LOL


#############################################
### EDIT VALUES HERE TO CONFIGURE THE BOT ###
#############################################

# STANDARD SETTINGS
_MAX_BEST_OF:int = 9
_REQUEST_TIMEOUT:float = 120.0
_DELETE_EXPIRED_REQUESTS:bool = False

# OBS INFO
_OBS_ENABLED:bool = True
_OBS_WEBSOCKET_PORT:int = 4444
_OBS_WEBSOCKET_PASSWORD:str = None # getenv("OBS_PASS")

# OBS SOURCE INFO
_OBS_VERSUS_SCENE_NAME:str = "Versus"
_OBS_GAME_SCENE_NAME:str = "Game"
_OBS_VERSUS_SONG_SOURCE_NAME:str = "VersusSong"
_OBS_FINALE_SONG_SOURCE_NAME:str = "FinaleSong"
_OBS_STRIKING_SOURCE_NAME:str = "striking.html"

# FUNCTION IMPLEMENTATIONS
def get_max_best_of() -> int:
    return _MAX_BEST_OF

def get_match_request_timeout() -> float:
    return _REQUEST_TIMEOUT

def get_delete_expired_requests() -> bool:
    return _DELETE_EXPIRED_REQUESTS

def get_obs_enabled() -> bool:
    return _OBS_ENABLED
def get_obs_port() -> int:
    return _OBS_WEBSOCKET_PORT
def get_obs_password() -> str:
    return _OBS_WEBSOCKET_PASSWORD
def get_versus_scene_name() -> str:
    return _OBS_VERSUS_SCENE_NAME
def get_game_scene_name() -> str:
    return _OBS_GAME_SCENE_NAME
def get_versus_song_name() -> str:
    return _OBS_VERSUS_SONG_SOURCE_NAME
def get_finale_song_name() -> str:
    return _OBS_FINALE_SONG_SOURCE_NAME
def get_striking_name() -> str:
    return _OBS_STRIKING_SOURCE_NAME