
# libs
import discord
import time, logging

from functions import *
from structs import *
from commands import *


# setup logging
logging.basicConfig(
	filename = CONFIG.LOG_FILE
	, encoding = "utf-8"
	, level = CONFIG.LOG_LEVEL
	, format = r"%(asctime)s - [%(levelname)s]: %(message)s"
	, datefmt=r"%d.%m.%Y %I:%M:%S %p"
)


# client class
class Client(discord.Client):
	
	# event: ready
	async def on_ready(self):
		print("ready")
		logging.info("ready")
	
	# event: member join
	async def on_member_join(self, member):
		logging.info("member joined")
		updateGuildData({"bots_count" if member.bot else "members_count": [1, "add"]}, member.guild.id)
	
	# event: member remover
	async def on_member_remove(self, member):
		logging.info("member removed")
		updateGuildData({"bots_count" if member.bot else "members_count": [1, "add"]}, member.guild.id)
		updateUserData({"leave_timestamp": [time.time()]}, member.id)
	
	# event: guild join
	async def on_guild_join(self, guild):
		logging.info("guild joined")

		bots_count, members_count = 0, 0
		for member in guild.members:
			if member.bot: bots_count += 1
			else:          members_count += 1
		
		updateGuildData({
			"bots_count": [bots_count, "add"]
			, "members_count": [members_count, "add"]
		}, guild.id)
	
	# event: guild remover
	async def on_guild_remove(self, guild):
		logging.info("guild removed")
		updateGuildData({"leave_timestamp": [time.time()]}, guild.id)
	
	# event: message
	async def on_message(self, message):
		content = message.content
		channel = message.channel
		author  = message.author
		guild   = message.guild
		
		logging.debug(f"(msg sent) {channel.name} - {author.display_name}: '{content}'")

		# update guild data
		updateGuildData({
			"messages_count" if content.startswith(COMMAND.PREFIX) else "commands_count": [1, "add"]
		}, guild.id)
		
		# update user data
		updateUserData({
			"messages_count" if content.startswith(COMMAND.PREFIX) else "commands_count":  [1, "add"]
			, "words_count":   [len(content.split(" ")), "add"]
			, "letters_count": [len(content), "add"]
		}, author.id)

		# skip conditions
		if author.id == client.user.id: return
		# elif message.channel.id != 1024250906499354655: return
		
		if content.startswith(COMMAND.PREFIX): await executeCommand(message)

	# event: message edit
	async def on_message_edit(self, before, after):
		logging.debug(f"(msg edited before) {before.channel.name} - {before.author.display_name}: '{before.content}'")
		logging.debug(f"(msg edited after)  {after.channel.name} - {after.author.display_name}: '{after.content}'")

	# event: message delete
	async def on_message_delete(self, message):
		logging.debug(f"(msg deleted) {message.channel.name} - {message.author.display_name}: '{message.content}'")


# run
client = Client(intents=discord.Intents.all())
client.run(TOKEN.DISCORD)
