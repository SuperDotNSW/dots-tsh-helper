import json, os

LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_PATH = LOCAL_DIR+"/config.json"

current_settings:dict = {
    'stream_manager_role_id' : 0
}

def get_stream_manager_role_id() -> int:
    return current_settings['stream_manager_role_id']

def load_from_file():
    global current_settings
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            current_settings = json.loads(f.read())
    else:
        save_to_file()
def save_to_file():
    global current_settings
    with open(CONFIG_PATH, "w") as f:
            json.dump(current_settings, f)

load_from_file()
print(get_stream_manager_role_id())