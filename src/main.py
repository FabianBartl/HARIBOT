
# libs
import nextcord
from nextcord.ext import commands
from nextcord import Member, Guild, Message, Interaction, SlashOption, File, Embed, Permissions, Role

import time, logging, sys, sqlite3, json, os
from datetime import datetime
from urllib.request import urlopen

from structs import BOTINFO, TOKEN, COLOR, CONFIG, DATABASE, LOG
from functions import *

#-------#
# setup #
#-------#

logging.basicConfig(
	level = LOG.LEVEL
	, encoding = "utf-8"
	, format = "%(asctime)s  [%(levelname)s]\t%(message)s"
	, datefmt = "%Y-%m-%d %H:%M:%S"
	, handlers = [
		logging.FileHandler(LOG.PATH)
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
	DATABASE.CONNECTION = sqlite3.connect(DATABASE.FILE)
	DATABASE.CURSOR = DATABASE.CONNECTION.cursor()
	logging.info("connection to database established")
	
@bot.event
async def on_ready():
	try:
		await bot.sync_all_application_commands()
		logging.info(f"synced all application commands")
	except Exception as e:
		logging.critical(e)
	logging.info("bot is ready")

@bot.event
async def on_close():
	DATABASE.CONNECTION.close()
	logging.warning("connection to database closed")
	logging.warning("bot was shut down")

@bot.event
async def on_disconnect():
	logging.warning("bot was disconnected")
	time.sleep(1)
	await bot.connect(reconnect=True)
	logging.info("reconnected after 1 second (now with reconnect flag)")

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

#-----#

@bot.slash_command(name="log", description="Manage logging files.", default_member_permissions=Permissions(administrator=True))
async def sc_log(
	interaction: Interaction
	, action: int = SlashOption(required=True, choices={"backup": 0, "save": 1, "get": 2, "clear": 3, "reset": 4})
):
	dstFile = f"log_{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}.dat"
	dstPath = os.path.abspath(os.path.join(LOG.DIR, dstFile))

	if action == 0: #backup: save, get, clear
		log_code, dstSize = backupLogFile(dstPath)
		msg = f"log of size `{dstSize/1000:.2f} KB` backuped as `{dstFile}`"
		await interaction.response.send_message(msg, file=File(dstPath, filename=dstFile), ephemeral=True)
		logging.info(f"log file backuped at {dstPath}")

	elif action == 1: #save
		dstSize = saveLogFile(dstPath)
		msg = f"log of size `{dstSize/1000:.2f} KB` saved as `{dstFile}`"
		await interaction.response.send_message(msg, ephemeral=True)
		logging.info(f"log file saved at {dstPath}")

	elif action == 2: #get
		log_code = getLogFile()
		msg = f"```js\n...\n{log_code}\n```"
		await interaction.response.send_message(msg, file=File(LOG.PATH, filename=dstFile), ephemeral=True)
		logging.debug(f"sent end of log file")
	
	elif action == 3: #clear
		if checkOwner(interaction.user.id):
			clearLogFile()
			msg = f"log file cleared"
		else:
			msg = f"no permission to use"
		
		await interaction.response.send_message(msg, ephemeral=True)
		logging.warning(msg)

	elif action == 4: #reset
		if checkOwner(interaction.user.id):
			logFiles = resetLogFiles()
			msg = f"all {len(logFiles)} log file(s) deleted / cleared"
		else:
			msg = f"no permission to use"
		
		await interaction.response.send_message(msg, ephemeral=True)
		logging.critical(msg)

	logging.debug(f"(command sent) log: {action=}")

#-----#

@bot.slash_command(name="member-info", description="Get information about a mentioned member.")
async def sc_memberInfo(
	interaction: Interaction
	, member: Member = SlashOption(required=False)
):
	if type(member) is not Member: member = interaction.user
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
async def sc_serverInfo(interaction: Interaction):
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
async def sc_botInfo(interaction: Interaction):
	app = await interaction.guild.fetch_member(BOTINFO.ID)

	embed = Embed(color=COLOR.SUCCESS, title="Bot Info", description=BOTINFO.DESCRIPTION)
	embed.set_thumbnail(url=app.display_avatar.url)
	embed.add_field(name="Name", value=f"{app.name}")
	embed.add_field(name="Creator", value=BOTINFO.CREATOR)
	embed.add_field(name="Joined at", value=app.joined_at.strftime("%d.%m.%Y %H:%M"))

	try:
		request = urlopen("https://api.github.com/repos/FabianBartl/HARIBOT/issues?state=all").read()
		issues_list = json.loads(request)
		logging.debug(f"(successfully requested issues) {issues_list}")

		labels_dict = dict()
		for issue in issues_list:
			if issue["state"] == "closed":
				labels_dict["Closed"] = labels_dict.get("Closed", 0) + 1
				continue
			for label in issue["labels"]:
				labels_dict[label["name"]] = labels_dict.get(label["name"], 0) + 1
		
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

@bot.slash_command(name="auto-role", description="Manage auto role.", default_member_permissions=Permissions(administrator=True))
async def sc_autoRole(
	interaction: Interaction
	, action: int = SlashOption(required=True, choices={"add": 0, "remove": 1, "list": 2})
	, type: int = SlashOption(required=True, choices={"User": 0, "Bot": 1})
	, role: Role = SlashOption(required=True)
):
	await interaction.response.send_message(f"`auto-role`: `{action=}`, `{role=}`, `{type=}`", ephemeral=CONFIG.EPHEMERAL)
	logging.debug(f"(command sent) auto-role: {action=}, {role=}, {type=}")


@bot.slash_command(name="reaction-role", description="Manage reaction role.")
async def sc_reactionRole(interaction: Interaction, message_id: int, emoji: int, role: int):
	await interaction.response.send_message(f"`reaction-role`: `{message_id=}`, `{emoji=}`, `{role=}`", ephemeral=CONFIG.EPHEMERAL)
	logging.debug(f"(command sent) reaction-role add: {message_id=}, {emoji=}, {role=}")

#---------#
# execute #
#---------#

if __name__ == "__main__": bot.run(TOKEN.DISCORD)
