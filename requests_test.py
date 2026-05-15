import requests
import random
from TSHObjects import State, Ruleset, Player

BASE_URL = "http://localhost:5000"

# REQUEST EXAMPLE
webdata = requests.get(f"{BASE_URL}/ruleset").json()
ruleset = Ruleset(webdata)
state = State(webdata)

teststage = ruleset.neutralStages[0]

print(teststage)

# POST EXAMPLE
# post = requests.post(f"{BASE_URL}/stage_strike_stage_clicked", json=teststage)
# post = requests.post(f"{BASE_URL}/stage_strike_reset")
# post = requests.post(f"{BASE_URL}/stage_strike_rps_win", json={'winner': random.randint(0, 1)})
# print(post)
