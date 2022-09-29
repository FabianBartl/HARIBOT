
# libs
import nextcord
from nextcord.ext import commands
from nextcord import Member, Guild, Message, Interaction, SlashOption, File, Embed, Permissions, Role, Emoji

import time, json, os
from datetime import datetime
from urllib.request import urlopen

from structs import BOTINFO, TOKEN, COLOR, CONFIG, LOG
from functions import *

#-------#
# setup #
#-------#

bot = commands.Bot(
	command_prefix = CONFIG.PREFIX
	, intents = nextcord.Intents.all()
)

setupLogger()

#--------#
# events #
#--------#

@bot.event
async def on_connect():
	LOG.LOGGER.info("bot connected")
	
@bot.event
async def on_ready():
	try:
		await bot.sync_all_application_commands()
		LOG.LOGGER.info(f"synced all application commands")
	except Exception as e:
		LOG.LOGGER.error(e)
	LOG.LOGGER.info("bot is ready")

@bot.event
async def on_close():
	LOG.LOGGER.critical("bot was shut down")

@bot.event
async def on_disconnect():
	LOG.LOGGER.warning("bot was disconnected")
	LOG.LOGGER.info("will be reconnected after 1 second (now with reconnect flag)")
	time.sleep(1)
	await bot.connect(reconnect=True)

#-----#

@bot.event
async def on_member_join(member: Member):
	LOG.LOGGER.info("member joined")
	updateGuildData({"bots_count" if member.bot else "users_count": [1, "add"]}, member.guild.id)

@bot.event
async def on_member_remove(member: Member):
	LOG.LOGGER.info("member removed")
	updateGuildData({"bots_count" if member.bot else "users_count": [1, "add"]}, member.guild.id)
	updateUserData({"leave_timestamp": [time.time()]}, member.id)

@bot.event
async def on_guild_join(guild: Guild):
	LOG.LOGGER.info("guild joined")

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
	LOG.LOGGER.info("guild removed")
	updateGuildData({"leave_timestamp": [time.time()]}, guild.id)

#-----#

@bot.event
async def on_message(message: Message):
	content = message.content
	channel = message.channel
	author  = message.author
	guild   = message.guild
	LOG.LOGGER.debug(f"(msg sent) {channel.name} - {author.display_name}: '{content}'")

	updateGuildData({
		"messages_count": [1, "add"]
		, "words_count": [len(content.split(" ")), "add"]
		, "letters_count": [len(content), "add"]
	}, guild.id)
	updateUserData({
		"messages_count": [1, "add"]
		, "words_count": [len(content.split(" ")), "add"]
		, "letters_count": [len(content), "add"]
	}, author.id)

@bot.event
async def on_message_edit(before: Message, after: Message):
	LOG.LOGGER.debug(f"(msg edited before) {before.channel.name} - {before.author.display_name}: '{before.content}'")
	LOG.LOGGER.debug(f"(msg edited after)  {after.channel.name} - {after.author.display_name}: '{after.content}'")

@bot.event
async def on_message_delete(message: Message):
	LOG.LOGGER.debug(f"(msg deleted) {message.channel.name} - {message.author.display_name}: '{message.content}'")

#----------#
# commands #
#----------#

@bot.slash_command(name="help", description="Overview of all commands.")
async def sc_help(interaction: Interaction):
	LOG.LOGGER.debug(f"(command sent) help")
	
	prefix = CONFIG.PREFIX
	embed = Embed(color=COLOR.INFO, title="Command Overview")
	
	for command in bot.walk_commands():
		name        = command.name
		description = command.description
		signature   = command.signature

		if not description or description is None or description == "": description = "*no description provided*"
		embed.add_field(name=f"`{prefix}{name}{signature if signature is not None else ''}`", value=description)
	
	await interaction.response.send_message(embed=embed, ephemeral=CONFIG.EPHEMERAL)

#-----#

@bot.slash_command(name="ping", description="Test bot response.")
async def sc_ping(interaction: Interaction):
	LOG.LOGGER.debug(f"(command sent) ping")
	await interaction.response.send_message(f"pong with `{bot.latency*1000:.0f} ms` latency", ephemeral=CONFIG.EPHEMERAL)

#-----#

@bot.slash_command(name="log", description="Manage logging files.", default_member_permissions=Permissions(administrator=True))
async def sc_log(
	interaction: Interaction
	, action: int = SlashOption(required=True, choices={"backup": 0, "save": 1, "get": 2, "clear": 3, "reset": 4})
):
	LOG.LOGGER.debug(f"(command sent) log: {action=}")

	dstFile = f"log_{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}.dat"
	dstPath = os.path.abspath(os.path.join(LOG.DIR, dstFile))

	if action == 0: #backup: save, get, clear
		log_code, dstSize = backupLogFile(dstPath)
		msg = f"log of size `{dstSize/1000:.2f} KB` backuped as `{dstFile}`"
		await interaction.response.send_message(msg, file=File(dstPath, filename=dstFile), ephemeral=True)

	elif action == 1: #save
		dstSize = saveLogFile(dstPath)
		msg = f"log of size `{dstSize/1000:.2f} KB` saved as `{dstFile}`"
		await interaction.response.send_message(msg, ephemeral=True)

	elif action == 2: #get
		log_code = getLogFile()
		msg = f"```js\n...\n{log_code}\n```"
		await interaction.response.send_message(msg, file=File(LOG.PATH, filename=dstFile), ephemeral=True)
	
	elif action == 3: #clear
		if checkOwner(interaction.user.id):
			clearLogFile()
			msg = f"log file cleared"
		else:
			msg = f"no permission to use"
		await interaction.response.send_message(msg, ephemeral=True)

	elif action == 4: #reset
		if checkOwner(interaction.user.id):
			logFiles = resetLogFiles()
			msg = f"all {len(logFiles)} log file(s) deleted / cleared"
		else:
			msg = f"no permission to use"
		await interaction.response.send_message(msg, ephemeral=True)

#-----#

@bot.slash_command(name="member-info", description="Get information about a mentioned member.")
async def sc_memberInfo(
	interaction: Interaction
	, member: Member = SlashOption(required=False)
):
	LOG.LOGGER.debug(f"(command sent) member-info: {member=}")

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


@bot.slash_command(name="server-info", description="Get information about this server.")
async def sc_serverInfo(interaction: Interaction):
	LOG.LOGGER.debug(f"(command sent) server-info")

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


@bot.slash_command(name="bot-info", description="Get information about this bot.")
async def sc_botInfo(interaction: Interaction):
	LOG.LOGGER.debug(f"(command sent) bot-info")

	app = await interaction.guild.fetch_member(BOTINFO.ID)

	embed = Embed(color=COLOR.SUCCESS, title="Bot Info", description=BOTINFO.DESCRIPTION)
	embed.set_thumbnail(url=app.display_avatar.url)
	embed.add_field(name="Name", value=f"{app.name}")
	embed.add_field(name="Creator", value=BOTINFO.CREATOR)
	embed.add_field(name="Joined at", value=app.joined_at.strftime("%d.%m.%Y %H:%M"))

	try:
		request = urlopen("https://api.github.com/repos/FabianBartl/HARIBOT/issues?state=all").read()
		issues_list = json.loads(request)
		LOG.LOGGER.debug(f"(successfully requested issues) {issues_list}")

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
		LOG.LOGGER.error(e)

	embed.add_field(name="GitHub", value=f"[{BOTINFO.REPOSITORY}](https://github.com/{BOTINFO.REPOSITORY})")
	embed.add_field(name="Invite", value=f"[private invite]({BOTINFO.INVITE})")

	embed.set_footer(text=f"Bot ID: {app.id}")

	await interaction.response.send_message(embed=embed, ephemeral=CONFIG.EPHEMERAL)

#-----#

@bot.slash_command(name="auto-role", description="Manage auto role.", default_member_permissions=Permissions(administrator=True))
async def sc_autoRole(
	interaction: Interaction
	, action: int = SlashOption(required=True, choices={"add": 0, "list": 1, "remove": 2, "clear": 3})
	, _type: int = SlashOption(required=True, choices={"User": 0, "Bot": 1}, name="type")
	, role: Role = SlashOption(required=True)
):
	LOG.LOGGER.debug(f"(command sent) auto-role: {action=}, {role=}, {_type=}")

	guild = interaction.guild
	
	if action == 0:
		updateGuildData({
			"auto-role_User": [1, "add"]
		}, guild.id)

	elif action == 1:
		pass

	elif action == 2:
		pass

	elif action == 3:
		pass

	await interaction.response.send_message(f"`auto-role`: `{action=}`, `{role=}`, `{_type=}`", ephemeral=CONFIG.EPHEMERAL)


@bot.slash_command(name="reaction-role", description="Manage reaction role.")
async def sc_reactionRole(
	interaction: Interaction
	, action: int = SlashOption(required=True, choices={"add": 0, "list": 1, "remove": 2, "clear": 3})
	, messageID: int = SlashOption(required=True)
	, emoji: int = SlashOption(required=True)
	, role: Role = SlashOption(required=True)
):
	LOG.LOGGER.debug(f"(command sent) reaction-role add: {action=}, {messageID=}, {emoji=}, {role=}")
	await interaction.response.send_message(f"`reaction-role`: `{action=}`, `{messageID=}`, `{emoji=}`, `{role}`", ephemeral=CONFIG.EPHEMERAL)

#---------#
# execute #
#---------#

if __name__ == "__main__": bot.run(TOKEN.DISCORD)
