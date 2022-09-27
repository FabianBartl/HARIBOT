
# libs
import discord
import os, json, time


#globals
class TOKEN:
	DISCORD = open(os.path.abspath(r"../discord.token"), "r").readlines()[0].strip()

class COLOR:
	BLUE      = 0x007BFF
	INDIGO    = 0x6610F2
	PURPLE    = 0x6F42C1
	PINK      = 0xE83E8C
	RED       = 0xE2001A
	ORANGE    = 0xFD7E14
	YELLOW    = 0xFFC107
	GREEN     = 0x28A745
	TEAL      = 0x20C997
	CYAN      = 0x17A2B8
	WHITE     = 0xFFFFFF
	GRAY      = 0x6C757D
	GRAY_DARK = 0x343A40
	PRIMARY   = 0x3390B4
	SECONDARY = 0x6C757D
	SUCCESS   = 0x28A745
	INFO      = 0x17A2B8
	WARNING   = 0xFFC107
	DANGER    = 0xE2001A
	LIGHT     = 0xF8F9FA
	DARK      = 0x343A40

class CONFIG:
	PREFIX = "/"
	INVITE = "https://discord.com/oauth2/authorize?client_id=1024235031037759500&permissions=8&scope=bot"
	DATA   = "../data"


# functions
def updateDataFile(newData, dataPath, fileID):
	filePath = os.path.abspath(f"{CONFIG.DATA}/{dataPath}/{fileID}.json")

	if not os.path.exists(filePath):
		with open(filePath, "w+") as fobj:
			fobj.write("{}")

	with open(filePath, "r") as fobj:
		oldData = json.load(fobj)
	
	for key in newData:
		if   len(newData[key]) == 1: value, mode = newData[key], "new"
		elif len(newData[key]) == 2: value, mode = newData[key]

		if key not in oldData: mode = "new"

		if   mode == "add": oldData[key] += value
		elif mode == "sub": oldData[key] -= value
		elif mode == "mul": oldData[key] *= value
		elif mode == "div": oldData[key] /= value

		elif mode == "new": oldData[key]  = value
		else:               oldData[key]  = value
	
	with open(filePath, "w") as fobj:
		json.dump(oldData, fobj)

def updateGuildData(newData, fileID): updateDataFile(newData, "guilds", fileID)
def updateUserData (newData, fileID): updateDataFile(newData, "users",  fileID)


def resolveCommand(clientObj, message):
	pass


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

		# skip conditions for commands
		if author.id == client.user.id: return
		# elif message.channel.id != 1024250906499354655: return
		else: resolveCommand(self, message)


# run
client = Client(intents=discord.Intents.all())
client.run(TOKEN.DISCORD)
