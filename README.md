# Dot's TSH Helper Bot
My first attempt at making a discord bot! This repository attempts to integrate TSH's stage banning app as a bot on discord for ease of running events that require stage-banning and want to intergrate closely with TSH's stage banning overlay.

### TODO:
- Allow for multiple stage pools that players can vote on when starting their set
- Support 'banByMaxGames' in TSH
- Create GameInstance that can interface directly with the current TSH stream match
- Allow for pulling ruleset(s) from .json files independent of TSH
- Add moderation commands for TOs to force winners or terminate matches by using an ID

## Dependencies:
- colorama           0.4.6    (Coloured messages in terminal)
- discord.py         2.7.1    (Discord API)
- requests           2.34.2   (Communicates with webapps)
- python-dotenv      1.2.2    (Used to store bot token privately)