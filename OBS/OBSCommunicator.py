from python_obs.clients import OBS
import config

if config.get_obs_enabled():
    obs:OBS = OBS(port=config.get_obs_port(), password=config.get_obs_password())
    obs.connect()

    versus_scene = obs.scene(config.get_versus_scene_name())
    game_scene = obs.scene(config.get_game_scene_name())
    versus_song_source = versus_scene.source(config.get_versus_song_name())
    finale_song_source = versus_scene.source(config.get_finale_song_name())

    def set_finale_music(enabled:bool=False):
        if enabled:
            versus_song_source.hide()
            finale_song_source.show()
        else:
            versus_song_source.show()
            finale_song_source.hide()

    def go_to_versus_scene():
        obs.set_scene(config.get_versus_scene_name())
    def go_to_game_scene():
        obs.set_scene(config.get_game_scene_name())
    
    def reconnect_obs():
        obs.connect()