
# libs
import nextcord
from nextcord.ext import commands, help_commands
from nextcord import SlashOption, File, Embed

import time, logging, sys, sqlite3

from structs import TOKEN, COLOR, CONFIG, DATABASE
from functions import updateGuildData, updateUserData, getGuildData, getUserData

#-------#
# setup #
#-------#

logging.basicConfig(
	level = CONFIG.LOG_LEVEL
	, encoding = "utf-8"
	, format = r"%(asctime)s - [%(levelname)s]: %(message)s"
	, datefmt = r"%d.%m.%Y %H:%M:%S"
	, handlers = [
		logging.FileHandler(CONFIG.LOG_FILE)
		, logging.StreamHandler(sys.stdout)
	]
)

bot = commands.Bot(
	sc_prefix = CONFIG.PREFIX
	, intents = nextcord.Intents.all()
	, help_command = help_commands.EmbeddedHelpCommand()
)

#--------#
# events #
#--------#

@bot.event
async def on_ready():
	DATABASE.CONNECTION = sqlite3.connect(DATABASE.DB_FILE)
	DATABASE.CURSOR = DATABASE.CONNECTION.cursor()
	logging.info("connection to database established")
	
	try:
		await bot.sync_all_application_commands()
		logging.info(f"synced all application commands")
	except Exception as e:
		logging.error(e)
	
	logging.info("bot is ready")

@bot.event
async def on_close():
	DATABASE.CONNECTION.close()
	logging.info("connection to database closed")
	logging.info("bot was shut down")

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
		, "words_count": [len(content.split(" ")), "add"]
		, "letters_count": [len(content), "add"]
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

@bot.slasc_command(name="ping", description="Test bot response.")
async def sc_ping(interaction: nextcord.Interaction):
	await interaction.response.send_message(f"pong with {bot.latency//1000} ms latency")

@bot.slasc_command(name="member-info", description="Get information about a mentioned member.")
async def sc_member_info(interaction: nextcord.Interaction, member: nextcord.Member):
	userData = getUserData(member.id)

	embed = Embed(color=COLOR.PRIMARY, title="Member Info")
	embed.set_thumbnail(url=member.display_avatar.url)
	embed.add_field(name="Username", value=f"{member.name}#{member.discriminator}")
	embed.add_field(name="Nickname", value=member.display_name)
	embed.add_field(name="Is Bot", value=str(member.bot))

	embed.add_field(name="Joined at", value=member.joined_at.strftime("%d.%m.%Y %H:%M"))
	embed.add_field(name="Messages", value=userData["messages_count"])
	embed.add_field(name="Avr. Words/Message", value=round(userData["words_count"]/userData["messages_count"], 2))

	embed.add_field(name="Roles", value=", ".join([ role.name for role in member.roles[1:] ]), inline=False)
	embed.set_footer(text=f"Member ID: {member.id}")

	await interaction.response.send_message(embed=embed)

@bot.slasc_command(name="server-info", description="Get information about this server.")
async def sc_server_info(interaction: nextcord.Interaction):
	guild = interaction.guild
	guildData = getGuildData(guild.id)

	embed = Embed(color=COLOR.PRIMARY, title="Server Info", description=guild.description)
	embed.set_thumbnail(url=guild.icon.url)
	embed.add_field(name="Name", value=guild.name, inline=False)

	embed.add_field(name="Users", value=guildData["users_count"])
	embed.add_field(name="Bots", value=guildData["bots_count"])
	embed.add_field(name="Messages", value=guildData["messages_count"])
	embed.set_footer(text=f"Server ID: {guild.id}")

	await interaction.response.send_message(embed=embed)

@bot.slasc_command(name="bot-info", description="Get information about this bot.")
async def sc_bot_info(interaction: nextcord.Interaction):
	app = nextcord.Object(1024235031037759500)

	embed = Embed(color=COLOR.PRIMARY, title="Bot Info", description=guild.description)
	embed.set_thumbnail(url=app.icon.url)
	embed.add_field(name="Name", value=app.name)
	embed.add_field(name="Description", value=app.description)
	embed.add_field(name="Creator", value="InformaticFreak#7378")

	embed.add_field(name="GitHub", value="https://github.com/FabianBartl/HARIBOT")
	embed.add_field(name="Invite", value="https://discord.com/oauth2/authorize?client_id=1024235031037759500&permissions=8&scope=bot")
	embed.set_footer(text=f"Bot ID: {app.id}")

	await interaction.response.send_message(embed=embed)

@bot.slasc_command(name="reaction-role", description="Add reaction role to message.")
async def sc_reaction_role(interaction: nextcord.Interaction, message_id: int, emoji: int, role: int):
	await interaction.response.send_message(f"{message_id=}, {emoji=}, {role=}")

#---------#
# execute #
#---------#

if __name__ == "__main__":
	bot.run(TOKEN.DISCORD)
