
# libs
import nextcord
from nextcord.ext import commands
from nextcord import Member, Guild, Message, Interaction, SlashOption, File, Embed, Permissions

import time, logging, sys, sqlite3, json, os
from datetime import datetime
from urllib.request import urlopen

from structs import BOTINFO, TOKEN, COLOR, CONFIG, DATABASE
from functions import *

#-------#
# setup #
#-------#

logging.basicConfig(
	level = CONFIG.LOG_LEVEL
	, encoding = "utf-8"
	, format = "%(asctime)s  [%(levelname)s]\t%(message)s"
	, datefmt = "%Y-%m-%d %H:%M:%S"
	, handlers = [
		logging.FileHandler(CONFIG.LOG_FILE)
		, logging.StreamHandler(sys.stdout)
	]
)

bot = commands.Bot(
	command_prefix = CONFIG.PREFIX
	, intents = nextcord.Intents.all()
)

#--------#
# events #
#--------#

@bot.event
async def on_connect():
	DATABASE.CONNECTION = sqlite3.connect(DATABASE.DB_FILE)
	DATABASE.CURSOR = DATABASE.CONNECTION.cursor()
	logging.info("connection to database established")
	
@bot.event
async def on_ready():
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
async def on_disconnect():
	logging.info("bot was disconnected")
	await time.sleep(3)
	await bot.connect(reconnect=True)
	logging.info("reconnected after 3 seconds")

#-----#

@bot.event
async def on_member_join(member: Member):
	logging.info("member joined")
	updateGuildData({"bots_count" if member.bot else "users_count": [1, "add"]}, member.guild.id)

@bot.event
async def on_member_remove(member: Member):
	logging.info("member removed")
	updateGuildData({"bots_count" if member.bot else "users_count": [1, "add"]}, member.guild.id)
	updateUserData({"leave_timestamp": [time.time()]}, member.id)

@bot.event
async def on_guild_join(guild: Guild):
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
async def on_guild_remove(guild: Guild):
	logging.info("guild removed")
	updateGuildData({"leave_timestamp": [time.time()]}, guild.id)

#-----#

@bot.event
async def on_message(message: Message):
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
async def on_message_edit(before: Message, after: Message):
	logging.debug(f"(msg edited before) {before.channel.name} - {before.author.display_name}: '{before.content}'")
	logging.debug(f"(msg edited after)  {after.channel.name} - {after.author.display_name}: '{after.content}'")

@bot.event
async def on_message_delete(message: Message):
	logging.debug(f"(msg deleted) {message.channel.name} - {message.author.display_name}: '{message.content}'")

#----------#
# commands #
#----------#

@bot.slash_command(name="help", description="Overview of all commands.")
async def sc_help(interaction: Interaction):
	prefix = CONFIG.PREFIX
	
	embed = Embed(color=COLOR.INFO, title="Command Overview")
	for command in bot.walk_commands():
		name        = command.name
		description = command.description
		signature   = command.signature

		if not description or description is None or description == "": description = "*no description provided*"
		
		embed.add_field(name=f"`{prefix}{name}{signature if signature is not None else ''}`", value=description)
	
	await interaction.response.send_message(embed=embed, ephemeral=CONFIG.EPHEMERAL)
	logging.debug(f"(command sent) help")

#-----#

@bot.slash_command(name="ping", description="Test bot response.")
async def sc_ping(interaction: Interaction):
	await interaction.response.send_message(f"pong with `{bot.latency*1000:.0f} ms` latency", ephemeral=CONFIG.EPHEMERAL)
	logging.debug(f"(command sent) ping")


@bot.slash_command(name="log", description="Manage logging file.", default_member_permissions=Permissions(administrator=True))
async def sc_log(interaction: Interaction, mode: int=SlashOption(required=True, choices={"backup": 0, "save": 1, "get": 2, "clear": 3}), arg: int=-1):
	dstFile = f"log_{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}.dat"
	dstPath = os.path.abspath(f"{CONFIG.LOG_DIR}/{dstFile}")

	if mode == 0: #backup: get, save, clear
		await sc_log(interaction, mode=2)
		await sc_log(interaction, mode=1)
		await sc_log(interaction, mode=3)
		await interaction.response.send_message(f"backuped log file", ephemeral=True)
		logging.debug(f"backuped log file")

	elif mode == 1: #save
		dstSize = saveLogFile(dstPath)
		await interaction.response.send_message(f"log of size `{dstSize/1000:.2f} KB` saved as: `{dstFile}`", ephemeral=True)
		logging.info(f"saved log file at {dstPath}")

	elif mode == 2: #get
		log_code = getLogFile(rows=20 if arg < 1 else arg).replace("`", "'")
		await interaction.response.send_message(f"```js\n...\n{log_code}\n```", file=File(CONFIG.LOG_FILE, filename=dstFile), ephemeral=True)
		logging.debug(f"sent log file part")
	
	elif mode == 3: #clear
		clearLogFile()
		await interaction.response.send_message(f"cleared log file", ephemeral=True)
		logging.info(f"cleared log file")

	logging.debug(f"(command sent) log: {mode=}")

#-----#

@bot.slash_command(name="member-info", description="Get information about a mentioned member.")
async def sc_member_info(interaction: Interaction, member: Member):
	userData = getUserData(member.id)

	embed = Embed(color=COLOR.SUCCESS, title="Member Info")
	embed.set_thumbnail(url=member.display_avatar.url)
	embed.add_field(name="Username", value=f"{member.name}#{member.discriminator}")
	embed.add_field(name="Nickname", value=member.display_name)
	embed.add_field(name="Is a Bot", value="Yes" if member.bot else "No")

	embed.add_field(name="Joined at", value=member.joined_at.strftime("%d.%m.%Y %H:%M"))
	embed.add_field(name="Messages", value=userData.get("messages_count", 0))
	embed.add_field(name="Words/Message", value=round(userData.get("words_count", 0) / userData.get("messages_count", 1), 2))

	embed.add_field(name="Roles", value=", ".join([ role.name for role in member.roles[1:] ]), inline=False)

	embed.set_footer(text=f"Member ID: {member.id}")

	await interaction.response.send_message(embed=embed, ephemeral=CONFIG.EPHEMERAL)
	logging.debug(f"(command sent) member-info: {member=}")


@bot.slash_command(name="server-info", description="Get information about this server.")
async def sc_server_info(interaction: Interaction):
	guild = interaction.guild
	guildData = getGuildData(guild.id)

	embed = Embed(color=COLOR.SUCCESS, title="Server Info", description=guild.description)
	embed.set_thumbnail(url=guild.icon.url)
	embed.add_field(name="Name", value=guild.name, inline=False)

	embed.add_field(name="Users", value=guildData.get("users_count", 0))
	embed.add_field(name="Bots", value=guildData.get("bots_count", 0))
	embed.add_field(name="Messages", value=guildData.get("messages_count", 0))

	embed.add_field(name="Invite", value=f"[open](https://discord.gg/GVs3hmCmmJ) or copy invite:\n```\nhttps://discord.gg/GVs3hmCmmJ\n```", inline=False)

	embed.set_footer(text=f"Server ID: {guild.id}")

	await interaction.response.send_message(embed=embed, ephemeral=CONFIG.EPHEMERAL)
	logging.debug(f"(command sent) server-info")


@bot.slash_command(name="bot-info", description="Get information about this bot.")
async def sc_bot_info(interaction: Interaction):
	app = await interaction.guild.fetch_member(BOTINFO.ID)

	embed = Embed(color=COLOR.SUCCESS, title="Bot Info", description=BOTINFO.DESCRIPTION)
	embed.set_thumbnail(url=app.display_avatar.url)
	embed.add_field(name="Name", value=f"{app.name}")
	embed.add_field(name="Creator", value=BOTINFO.CREATOR)
	embed.add_field(name="Joined at", value=app.joined_at.strftime("%d.%m.%Y %H:%M"))

	try:
		request = urlopen("https://api.github.com/repos/FabianBartl/HARIBOT/issues").read()
		issues_list = json.loads(request)
		logging.debug(f"(successfully requested issues) {issues_list}")

		labels_dict = dict()
		for issue in issues_list:
			for label in issue["labels"]:
				num = labels_dict.get(label["name"], 0)
				labels_dict[label["name"]] = num + 1
		
		issues_value = ", ".join([ f"{label}: {labels_dict[label]}" for label in labels_dict ]).title()
		embed.add_field(name=f"Issue Tracker", value=f"{issues_value}, [see all](https://github.com/{BOTINFO.REPOSITORY}/issues)", inline=False)
	
	except Exception as e:
		logging.error(e)

	embed.add_field(name="GitHub", value=f"[{BOTINFO.REPOSITORY}](https://github.com/{BOTINFO.REPOSITORY})")
	embed.add_field(name="Invite", value=f"[private invite]({BOTINFO.INVITE})")

	embed.set_footer(text=f"Bot ID: {app.id}")

	await interaction.response.send_message(embed=embed, ephemeral=CONFIG.EPHEMERAL)
	logging.debug(f"(command sent) bot-info")

#-----#

@bot.slash_command(name="reaction-role", description="Add reaction role to message.")
async def sc_reaction_role(interaction: Interaction, message_id: int, emoji: int, role: int):
	await interaction.response.send_message(f"{message_id=}, {emoji=}, {role=}", ephemeral=CONFIG.EPHEMERAL)
	logging.debug(f"(command sent) reaction-role: {message_id=}, {emoji=}, {role=}")

#---------#
# execute #
#---------#

if __name__ == "__main__": bot.run(TOKEN.DISCORD)
