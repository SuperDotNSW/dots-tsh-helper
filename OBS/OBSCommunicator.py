from python_obs.clients import OBS
from python_obs.scene import Scene
from python_obs.source import Source
import config

obs:OBS = OBS(port=config.get_obs_port(), password=config.get_obs_password())

versus_scene:Scene
game_scene:Scene
versus_song_source:Source
finale_song_source:Source
striking_source:Source

def set_finale_music(enabled:bool=False):
    global versus_song_source, finale_song_source
    if not config.get_obs_enabled(): return
    if enabled:
        versus_song_source.hide()
        finale_song_source.show()
    else:
        versus_song_source.show()
        finale_song_source.hide()

def set_striking_visibility(visible:bool):
    global striking_source
    if not config.get_obs_enabled(): return
    if visible:
        striking_source.show()
    else:
        striking_source.hide()

def go_to_versus_scene():
    if not config.get_obs_enabled(): return
    obs.set_scene(config.get_versus_scene_name())
def go_to_game_scene():
    if not config.get_obs_enabled(): return
    obs.set_scene(config.get_game_scene_name())

def initalize_obs():
    global versus_scene, game_scene, versus_song_source, finale_song_source, striking_source
    if not config.get_obs_enabled(): return
    obs.connect()
    
    versus_scene = obs.scene(config.get_versus_scene_name())
    game_scene = obs.scene(config.get_game_scene_name())
    versus_song_source = versus_scene.source(config.get_versus_song_name())
    finale_song_source = versus_scene.source(config.get_finale_song_name())
    striking_source = versus_scene.source(config.get_striking_name())