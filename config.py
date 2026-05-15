import json, os

LOCAL_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_PATH = LOCAL_DIR+"/config.json"

current_settings:dict = {

}

def load_from_file():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            current_settings = json.loads(f.read())
    else:
        save_to_file()
def save_to_file():
    with open(CONFIG_PATH, "w") as f:
            json.dump(current_settings, f)

load_from_file()
