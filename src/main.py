
# libs
import nextcord
from nextcord.ext import commands
from nextcord import slash_command, SlashOption, File, ButtonStyle, Embed

import time, logging

from structs import TOKEN, COLOR, CONFIG
from functions import updateGuildData, updateUserData, getGuildData, getUserData

#-------#
# setup #
#-------#

logging.basicConfig(
	filename = CONFIG.LOG_FILE
	, encoding = "utf-8"
	, level = CONFIG.LOG_LEVEL
	, format = r"%(asctime)s - [%(levelname)s]: %(message)s"
	, datefmt=r"%d.%m.%Y %H:%M:%S"
)

bot = commands.Bot(
	command_prefix = CONFIG.PREFIX
	, intents = nextcord.Intents.all()
)

#--------#
# events #
#--------#

@bot.event
async def on_ready():
	print("ready")
	logging.info("ready")
	# sync slash commands 
	try:
		synced = await bot.sync_all_application_commands()
		logging.info(f"synced all application commands")
	except Exception as e:
		logging.error(e)

@bot.event
async def on_member_join(member: nextcord.Member):
	logging.info("member joined")
	updateGuildData({"bots_count" if member.bot else "users_count": [1, "add"]}, member.guild.id)

@bot.event
async def on_member_remove(member: nextcord.Member):
	logging.info("member removed")
	updateGuildData({"bots_count" if member.bot else "users_count": [1, "add"]}, member.guild.id)
	updateUserData({"leave_timestamp": [time.time()]}, member.id)

@bot.event
async def on_guild_join(guild: nextcord.Guild):
	logging.info("guild joined")

	bots_count, users_count = 0, 0
	for member in guild.members:
		if member.bot: bots_count += 1
		else:          users_count += 1
	
	updateGuildData({
		"bots_count": [bots_count, "add"]
		, "users_count": [users_count, "add"]
	}, guild.id)

@bot.event
async def on_guild_remove(guild: nextcord.Guild):
	logging.info("guild removed")
	updateGuildData({"leave_timestamp": [time.time()]}, guild.id)

@bot.event
async def on_message(message: nextcord.Message):
	content = message.content
	channel = message.channel
	author  = message.author
	guild   = message.guild
	
	logging.debug(f"(msg sent) {channel.name} - {author.display_name}: '{content}'")

	# update guild data
	updateGuildData({
		"messages_count": [1, "add"]
	}, guild.id)
	
	# update user data
	updateUserData({
		"messages_count": [1, "add"]
		, "words_count": [len(content.split(" ")), "add"]
		, "letters_count": [len(content), "add"]
	}, author.id)

@bot.event
async def on_message_edit(before: nextcord.Message, after: nextcord.Message):
	logging.debug(f"(msg edited before) {before.channel.name} - {before.author.display_name}: '{before.content}'")
	logging.debug(f"(msg edited after)  {after.channel.name} - {after.author.display_name}: '{after.content}'")

@bot.event
async def on_message_delete(message: nextcord.Message):
	logging.debug(f"(msg deleted) {message.channel.name} - {message.author.display_name}: '{message.content}'")

#----------#
# commands #
#----------#

@bot.slash_command(name="ping", description="Test bot response.")
async def command_ping(interaction: nextcord.Interaction):
	await interaction.response.send_message(f"pong with {bot.latency:.2f} ms latency")

@bot.slash_command(name="user-info", description="Get information about a user.")
async def command_user_info(interaction: nextcord.Interaction, user: nextcord.Member):
	userData = getUserData(user.id)

	embed = Embed(color=COLOR.PRIMARY, title=("Bot" if user.bot else "User")+" Info")
	embed.set_thumbnail(url=user.display_avatar.url)
	embed.add_field(name="Username", value=f"{user.name}#{user.discriminator}")
	embed.add_field(name="Nickname", value=user.display_name)
	embed.add_field(name="Joined at", value=user.joined_at.strftime("%d.%m.%Y %H:%M"))
	embed.add_field(name="Messages", value=userData["messages_count"])
	embed.add_field(name="Avr. Words/Message", value=round(userData["words_count"]/userData["messages_count"], 2))
	embed.add_field(name="Roles", value=", ".join([ role.name for role in user.roles[1:] ]), inline=False)
	embed.set_footer(text=("Bot" if user.bot else "User")+f" ID: {user.id}")

	await interaction.response.send_message(embed=embed)

@bot.slash_command(name="server-info", description="Get information about this server.")
async def command_server_info(interaction: nextcord.Interaction):
	guild = interaction.guild
	guildData = getGuildData(guild.id)
	# nextcord.Interaction.guild.

	embed = Embed(color=COLOR.PRIMARY, title="Server Info", description=guild.description)
	embed.set_thumbnail(url=guild.icon.url)
	embed.add_field(name="Name", value=guild.name, inline=False)
	embed.add_field(name="Users", value=guildData["users_count"])
	embed.add_field(name="Bots", value=guildData["bots_count"])
	embed.add_field(name="Messages", value=guildData["messages_count"])
	embed.set_footer(text=f"Server ID: {guild.id}")

	await interaction.response.send_message(embed=embed)

#---------#
# execute #
#---------#

if __name__ == "__main__": bot.run(TOKEN.DISCORD)
