
# libs
import discord
import os, json, time

from functions import *
from structs import *


# client
class Client(discord.Client):
	
	# event: ready
	async def on_ready(self):
		print("ready")
	
	# event: member join
	async def on_member_join(self, member):
		updateGuildData({"bots_count" if member.bot else "members_count": [1, "add"]}, member.guild.id)
	
	# event: member remover
	async def on_member_remove(self, member):
		updateGuildData({"bots_count" if member.bot else "members_count": [1, "add"]}, member.guild.id)
		updateUserData({"leave_timestamp": [time.time()]}, member.id)
	
	# event: guild join
	async def on_guild_join(self, guild):
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
		updateGuildData({"leave_timestamp": [time.time()]}, guild.id)
	
	# event: message
	async def on_message(self, message):
		content = message.content
		channel = message.channel
		author  = message.author
		guild   = message.guild
		
		# update guild data
		updateGuildData({
			"messages_count": [1, "add"]
		}, guild.id)
		
		# update user data
		updateUserData({
			"messages_count":  [1, "add"]
			, "words_count":   [len(content.split(" ")), "add"]
			, "letters_count": [len(content), "add"]
		}, author.id)

		# log
		print(f"{channel.name} - {author.name}: '{content}'")

		# skip conditions
		if author.id == client.user.id: return
		# elif message.channel.id != 1024250906499354655: return
		
		if content.startswith("!"): executeCommand(self, message)


# run
client = Client(intents=discord.Intents.all())
client.run(TOKEN.DISCORD)
