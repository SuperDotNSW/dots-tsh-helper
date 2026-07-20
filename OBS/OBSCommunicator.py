from python_obs.clients import OBSAsync
from python_obs.scene import Scene
from python_obs.source import Source
import config
import websockets

# I should've just made this a class but whatever

obs:OBSAsync = None

versus_scene:Scene
game_scene:Scene
versus_song_source:Source
finale_song_source:Source
results_song_source:Source
striking_source:Source

SONG_VERSUS=0
SONG_FINALE=1
SONG_RESULTS=2

async def initalize_obs():
    global obs, versus_scene, game_scene, versus_song_source, finale_song_source, striking_source, results_song_source
    if not config.get_obs_enabled(): return

    obs = OBSAsync(port=config.get_obs_port(), password=config.get_obs_password())
    await obs.connect()
    
    versus_scene = obs.scene(config.get_versus_scene_name())
    game_scene = obs.scene(config.get_game_scene_name())
    versus_song_source = versus_scene.source(config.get_versus_song_name())
    finale_song_source = versus_scene.source(config.get_finale_song_name())
    results_song_source = versus_scene.source(config.get_results_song_name())
    striking_source = versus_scene.source(config.get_striking_name())

async def revive_connection():
    if not obs._client.ws:
        print("Attempting to connect to OBS...")
        await initalize_obs()
        return
    if obs._client.ws.state != 1:
        print(obs._client.ws.state)
        print("Connection Lost with OBS, attempting reconnection now.")
        await initalize_obs()

async def set_music(song_id:int=0):
    if not config.get_obs_enabled(): return
    await revive_connection()

    if song_id == SONG_VERSUS:
        await versus_song_source.show()
        await finale_song_source.hide()
        await results_song_source.hide()
        return
    elif song_id == SONG_FINALE:
        await versus_song_source.hide()
        await finale_song_source.show()
        await results_song_source.hide()
        return
    elif song_id == SONG_RESULTS:
        await versus_song_source.hide()
        await finale_song_source.hide()
        await results_song_source.show()
        return

async def set_striking_visibility(visible:bool):
    if not config.get_obs_enabled(): return
    await revive_connection()

    if visible:
        await striking_source.show()
    else:
        await striking_source.hide()

async def go_to_versus_scene():
    if not config.get_obs_enabled(): return
    await revive_connection()

    await obs.set_scene(config.get_versus_scene_name())
async def go_to_game_scene():
    if not config.get_obs_enabled(): return
    await revive_connection()

    await obs.set_scene(config.get_game_scene_name())

