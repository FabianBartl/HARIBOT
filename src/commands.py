
import logging, shlex
from structs import *
from functions import *

# https://stackoverflow.com/questions/49723047/parsing-a-string-as-a-python-argument-list

class EXECUTE:
	async def unknownCommand(self, message, command, content):
		logging.debug("unknownCommand")

		channel = message.channel
		author  = message.author
		args = shlex.split(content)

		await channel.send(f"unknownCommand: {args}")

	async def ping(self, message, command, content):
		logging.debug("ping")
		await message.channel.send("pong")

	async def userInfo(self, message, command, content, userID=False):
		logging.debug("userInfo")

	async def guildInfo(self, message, command, content):
		logging.debug("guildInfo")

