
# libs
import discord
import re, os
import random


#globals
class TOKEN:
    DISCORD = open(os.path.abspath(r"../discord.token"), "r").readlines()[0].strip()

class COLOR:
    BLUE = 0x007BFF
    INDIGO = 0x6610F2
    PURPLE = 0x6F42C1
    PINK = 0xE83E8C
    RED = 0xE2001A
    ORANGE = 0xFD7E14
    YELLOW = 0xFFC107
    GREEN = 0x28A745
    TEAL = 0x20C997
    CYAN = 0x17A2B8
    WHITE = 0xFFF
    GRAY = 0x6C757D
    GRAY_DARK = 0x343A40
    PRIMARY = 0x3390B4
    SECONDARY = 0x6C757D
    SUCCESS = 0x28A745
    INFO = 0x17A2B8
    WARNING = 0xFFC107
    DANGER = 0xE2001A
    LIGHT = 0xF8F9FA
    DARK = 0x343A40

class CONFIG:
    PREFIX = r"/"
    INVITE = r"https://discord.com/oauth2/authorize?client_id=1024235031037759500&permissions=8&scope=bot"


# client
class MyClient(discord.Client):
	
	# event: ready
	async def on_ready(self):
		print("ready")
	
	# event: message
	async def on_message(self, message):
		if not message.author is client.user: return

        print("event: on message")

# run
client = MyClient()
client.run(TOKEN.DISCORD)
