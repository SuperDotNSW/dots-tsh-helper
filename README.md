# Dot's TSH Helper Bot
My first attempt at making a discord bot! This repository attempts to integrate TSH's stage banning app as a bot on discord for ease of running events that require stage-banning and want to intergrate closely with TSH's stage banning overlay.

### TODO:
- Allow for multiple stage pools that players can vote on when starting their set
- Support 'banByMaxGames' in TSH
- Allow for pulling ruleset(s) from .json files independent of TSH
- Figure out how to auto-reconnect with OBS when the websocket connection drops/times out

## How to use:
- Create a virtual environment in the repo folder and activate it
```
python -m venv venv
source venv/bin/activate
```
- Install dependencies
```
pip install colorama discord.py requests python-dotenv python-obs
```
- Define TOKEN and OBS_PASS in a .env file
Example:
```
TOKEN=YOUR_BOT_TOKEN_HERE
OBS_PASS=YOUR_OBS_WEBSOCKET_PASSWORD_HERE
```
- Configure config.py (i couldn't be bothered to make a .json config serializer lmfao)
- Ensure Tournament Stream Helper is running and has a configured ruleset
- Run the bot
- Use `/start_match` in discord to get started!

## Dependencies:
- colorama           0.4.6    (Coloured messages in terminal)
- discord.py         2.7.1    (Discord API)
- requests           2.34.2   (Communicates with webapps)
- python-dotenv      1.2.2    (Used to store bot token privately)
- python-obs         1.3.0    (Used to integrate with OBS websockets)
