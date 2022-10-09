
# libs
import nextcord
from nextcord.ext import commands
from nextcord import Member, User, Guild, Message, Interaction, SlashOption, File, Embed, Permissions, Role, Reaction, Emoji, VoiceState

import time, json, os, sys, logging
from datetime import datetime
from urllib.request import urlopen

from structs import BOTINFO, TOKEN, HARIBO, CONFIG, LOG
from functions import *

#-------#
# setup #
#-------#

bot = commands.Bot(
	command_prefix = CONFIG.PREFIX
	, intents = nextcord.Intents.all()
)

colored = (len(sys.argv) >= 2 and sys.argv[1] == "colored")
level = int(sys.argv[2]) if len(sys.argv) >= 3 and sys.argv[2].isdigit() else logging.INFO

setupLogger(colored, level)

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
	LOG.LOGGER.info("will be reconnected after 5 seconds (now with reconnect flag)")
	time.sleep(5)
	await bot.connect(reconnect=True)

#-----#

@bot.event
async def on_member_join(member: Member):
	guild = member.guild
	_type = "bot" if member.bot else "user"
	LOG.LOGGER.info(f"member ({_type}) joined")

	updateGuildData({"bots" if _type == "bot" else "users": [1, "add"], "xp": [XP.DEFAULT, "add"]}, member.guild.id)
	updateUserData({"leave_timestamp": [None, "del"], "xp": [XP.DEFAULT, "add"]}, member.id)

	auto_role_IDs = getGuildData(guild.id).get(f"auto-roles_{_type}")
	roles = [ guild.get_role(roleID) for roleID in auto_role_IDs if guild.get_role(roleID) is not None ]
	role_mentions = [ role.mention for role in roles ]
	for role in roles: await member.add_roles(role)
	LOG.LOGGER.info(f"member ({_type}) gets following roles: {' '.join(role_mentions)}")


@bot.event
async def on_member_remove(member: Member):
	_type = "bot" if member.bot else "user"
	LOG.LOGGER.info(f"member ({_type}) removed")
	updateGuildData({f"{_type}s", [1, "sub"]}, member.guild.id)
	updateUserData({"leave_timestamp": [time.time(), "set"]}, member.id)


@bot.event
async def on_guild_join(guild: Guild):
	LOG.LOGGER.info("guild joined")

	bots, users = 0, 0
	for member in guild.members:
		if member.bot: bots += 1
		else:          users += 1
	
	updateGuildData({
		"bots": [bots, "add"]
		, "users": [users, "add"]
		, "leave_timestamp": [None, "del"]
	}, guild.id)


@bot.event
async def on_guild_remove(guild: Guild):
	LOG.LOGGER.info("guild removed")
	updateGuildData({"leave_timestamp": [time.time(), "set"]}, guild.id)

#-----#

@bot.event
async def on_reaction_add(reaction: Reaction, user: Member):
	guild   = reaction.message.guild
	message = reaction.message
	emoji   = reaction.emoji
	LOG.LOGGER.info(f"(reaction added) {message.id}: '{user.display_name}: {emoji}'")

	updateGuildData({"reactions": [1, "add"]}, guild.id)
	updateUserData ({"reactions": [1, "add"]}, user.id)


@bot.event
async def on_reaction_remove(reaction: Reaction, user: User):
	guild   = reaction.message.guild
	message = reaction.message
	emoji   = reaction.emoji
	LOG.LOGGER.debug(f"(reaction removed) {message.id}: '{user.display_name}: {emoji}'")

	updateGuildData({"reactions": [1, "sub"]}, guild.id)
	updateUserData ({"reactions": [1, "sub"]}, user.id)


@bot.event
async def on_reaction_clear(message: Message, reactions: list[Reaction, ]):
	emojis  = f"{reactions.message.author.display_name}:\n"
	emojis += ", ".join([ f"`{reaction.emoji}`" for reaction in reactions ])
	LOG.LOGGER.debug(f"(reaction cleared) {message.id}: '{emojis}'")


@bot.event
async def on_reaction_clear_emoji(reaction: Reaction):
	user    = reaction.message.author
	message = reaction.message
	emoji   = reaction.emoji
	LOG.LOGGER.debug(f"(reaction cleared emoji) {message.id}: '{user.display_name}: {emoji}'")

#-----#

@bot.event
async def on_message(message: Message):
	attachments = message.attachments
	content     = message.content
	channel     = message.channel
	author      = message.author
	guild       = message.guild
	LOG.LOGGER.debug(f"(msg sent) {channel.name} - {author.display_name}: {f'({len(attachments)} Attachments)' if len(attachments) > 0 else ''} '{content}'")
	
	words               = len(re.sub(" +", " ", content).split(" "))
	letters             = len(content)
	last_message        = time.time()

	user_data = getUserData(author.id)
	last_message_before = user_data.get("last_message", 0)
	xp_before           = user_data.get("xp", 0)

	xp  = xp_before
	xp += XP.DEFAULT if xp < XP.DEFAULT else 0
	xp += XP.GENERATE(last_message_before, last_message)
	LOG.LOGGER.debug(f"(xp earned) {author.display_name}: {xp}")

	updateGuildData({
		"messages": [1, "add"]
		, "words": [words, "add"]
		, "letters": [letters, "add"]
		, "attachments": [len(attachments), "add"]
		, "xp": [xp, "set"]
	}, guild.id)
	updateUserData({
		"messages": [1, "add"]
		, "words": [words, "add"]
		, "letters": [letters, "add"]
		, "attachments": [len(attachments), "add"]
		, "xp": [xp, "set"]
		, "last_message": [last_message, "set" if XP.COOLDOWN_ELAPSED(last_message_before, last_message) else "ign"]
	}, author.id)


@bot.event
async def on_message_edit(before: Message, after: Message):
	author = before.author
	guild  = before.guild
	LOG.LOGGER.debug(f"(msg edits before) {before.channel.name} - {before.author.display_name}: '{before.content}'")
	LOG.LOGGER.debug(f"(msg edits after)  {after.channel.name} - {after.author.display_name}: '{after.content}'")

	changes     = abs(len(after.content) - len(before.content))
	attachments = len(after.attachments) - len(before.attachments)
	words       = len(re.sub(" +", " ", after.content).split(" ")) - len(re.sub(" +", " ", before.content).split(" "))
	letters     = len(after.content) - len(before.content)

	updateGuildData({
		"edits": [1, "add"]
		, "changes_lenght": [changes, "add"]
		, "words": [words, "add"]
		, "letters": [letters, "add"]
		, "attachments": [attachments, "add"]
	}, guild.id)
	updateUserData({
		"edits": [1, "add"]
		, "changes_lenght": [changes, "add"]
		, "words": [words, "add"]
		, "letters": [letters, "add"]
		, "attachments": [attachments, "add"]
	}, author.id)


@bot.event
async def on_message_delete(message: Message):
	author  = message.author
	guild   = message.guild
	content = message.content
	LOG.LOGGER.debug(f"(msg deleted) {message.channel.name} - {message.author.display_name}: '{message.content}'")

	attachments = len(message.attachments)
	words       = len(re.sub(" +", " ", content).split(" "))
	letters     = len(content)

	updateGuildData({
		"deleted": [1, "add"]
		, "words": [words, "sub"]
		, "letters": [letters, "sub"]
		, "attachments": [attachments, "sub"]
	}, guild.id)
	updateUserData({
		"deleted": [1, "add"]
		, "words": [words, "sub"]
		, "letters": [letters, "sub"]
		, "attachments": [attachments, "sub"]
	}, author.id)

#-----#

@bot.event
async def on_presence_update(before: Member, after: Member):
	pass


@bot.event
async def on_user_update(before: User, after: User):
	pass


@bot.event
async def on_voice_state_update(member: Member, before: VoiceState, after: VoiceState):
	pass

#----------#
# commands #
#----------#

@bot.slash_command(name="help", description="Overview of all commands.")
async def sc_help(interaction: Interaction):
	LOG.LOGGER.debug(f"(command sent) help")
	
	updateGuildData({"commands": [1, "add"]}, interaction.guild.id)
	updateUserData({"commands": [1, "add"]}, interaction.user.id)

	prefix = CONFIG.PREFIX
	embed = Embed(color=int(HARIBO.INFO), title="Command Overview")
	
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
	
	updateGuildData({"commands": [1, "add"]}, interaction.guild.id)
	updateUserData({"commands": [1, "add"]}, interaction.user.id)

	latency = bot.latency
	msg = f"`{latency*1000:.0f} ms` latency"
	if   latency > 400: LOG.LOGGER.warning(msg)
	elif latency > 900: LOG.LOGGER.critical(msg)

	await interaction.response.send_message(f"pong with {msg}", ephemeral=True)

#-----#

@bot.slash_command(name="score", description="Get the score of a mentioned member.")
async def sc_memberInfo(
	interaction: Interaction
	, member: Member = SlashOption(required=False)
	, formatID: int = SlashOption(required=False, choices={"SVG": 0, "PNG": 1}, default=1, name="format")
):
	LOG.LOGGER.debug(f"(command sent) score: {member=}")
	
	updateGuildData({"commands": [1, "add"]}, interaction.guild.id)
	updateUserData({"commands": [1, "add"]}, interaction.user.id)
	
	if type(member) is not Member: member = interaction.user
	format = ["svg", "png"][formatID]

	score_card_file = createScoreCard(member)
	
	await interaction.response.send_message(file=File(score_card_file(format)), ephemeral=CONFIG.EPHEMERAL)

	os.system(f"del {score_card_file('*')}")
	LOG.LOGGER.warning(f"deleted temp score card files `{score_card_file('*')}`")

#-----#

@bot.slash_command(name="log", description="Manage logging files.", default_member_permissions=Permissions(administrator=True))
async def sc_log(
	interaction: Interaction
	, action: int = SlashOption(required=True, choices={"backup": 0, "save": 1, "get": 2, "clear": 3, "reset": 4, "list": 5})
):
	LOG.LOGGER.debug(f"(command sent) log: {action=}")
	
	updateGuildData({"commands": [1, "add"]}, interaction.guild.id)
	updateUserData({"commands": [1, "add"]}, interaction.user.id)

	msg = ""
	file = None
	dstFile = f"log_{datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}.dat"
	dstPath = os.path.abspath(os.path.join(LOG.DIR, dstFile))

	if action == 0: #backup: save, get, clear
		log_code, dstSize = backupLogFile(dstPath)
		msg = f"log of size `{formatBytes(dstSize)}` backuped as `{dstFile}`"
		file = File(dstPath, filename=dstFile)

	elif action == 1: #save
		dstSize = saveLogFile(dstPath)
		msg = f"log of size `{formatBytes(dstSize)}` saved as `{dstFile}`"

	elif action == 2: #get
		log_code = getLogFile().replace("`", "'")
		msg = f"```cmd\n...\n{log_code}\n```"
		file = File(LOG.PATH, filename=dstFile)
	
	elif action == 3: #clear
		if checkOwner(interaction.user.id):
			clearLogFile()
			msg = f"log file cleared"
		else:
			msg = f"no permission to use"

	elif action == 4: #reset
		if checkOwner(interaction.user.id):
			logFiles = resetLogFiles()
			msg = f"all {len(logFiles)} log file(s) deleted / cleared"
		else:
			msg = f"no permission to use"
	
	elif action == 5: #list
		logFiles = os.scandir(LOG.DIR)
		msg  = "```cmd\n"
		msg += "\n".join([ f"{formatBytes(file.stat().st_size):>10} | {file.name}" for file in logFiles ])
		msg += "\n```"
	
	if file: await interaction.response.send_message(msg, file=file, ephemeral=True)
	else:    await interaction.response.send_message(msg, ephemeral=True)

#-----#

@bot.slash_command(name="member-info", description="Get information about a mentioned member.")
async def sc_memberInfo(
	interaction: Interaction
	, member: Member = SlashOption(required=False)
):
	LOG.LOGGER.debug(f"(command sent) member-info: {member=}")
	
	updateGuildData({"commands": [1, "add"]}, interaction.guild.id)
	updateUserData({"commands": [1, "add"]}, interaction.user.id)

	if type(member) is not Member: member = interaction.user
	userData = getUserData(member.id)

	embed = Embed(color=int(HARIBO.SUCCESS), title="Member Info")
	embed.set_thumbnail(url=member.display_avatar.url)
	embed.add_field(name="Username", value=f"{member.name}#{member.discriminator}")
	embed.add_field(name="Nickname", value=member.display_name)
	embed.add_field(name="Is a Bot", value="Yes" if member.bot else "No")

	embed.add_field(name="Joined at", value=member.joined_at.strftime("%d.%m.%Y %H:%M"))
	embed.add_field(name="Messages", value=userData.get("messages", 0))
	embed.add_field(name="Words/Message", value=round(userData.get("words", 0) / userData.get("messages", 1), 2))

	embed.add_field(name="Roles", value=" ".join([ role.mention for role in member.roles[1:] ]), inline=False)
	embed.set_footer(text=f"Member ID: {member.id}")

	await interaction.response.send_message(embed=embed, ephemeral=CONFIG.EPHEMERAL)


@bot.slash_command(name="server-info", description="Get information about this server.")
async def sc_serverInfo(interaction: Interaction):
	LOG.LOGGER.debug(f"(command sent) server-info")
	
	updateGuildData({"commands": [1, "add"]}, interaction.guild.id)
	updateUserData({"commands": [1, "add"]}, interaction.user.id)

	guild = interaction.guild
	guildData = getGuildData(guild.id)

	embed = Embed(color=int(HARIBO.SUCCESS), title="Server Info", description=guild.description)
	embed.set_thumbnail(url=guild.icon.url)
	embed.add_field(name="Name", value=guild.name, inline=False)

	embed.add_field(name="Users", value=guildData.get("users", 0))
	embed.add_field(name="Bots", value=guildData.get("bots", 0))
	embed.add_field(name="Messages", value=guildData.get("messages", 0))

	embed.add_field(name="Invite", value=f"[open](https://discord.gg/GVs3hmCmmJ) or copy invite:\n```\nhttps://discord.gg/GVs3hmCmmJ\n```", inline=False)
	embed.set_footer(text=f"Server ID: {guild.id}")

	await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.slash_command(name="bot-info", description="Get information about this bot.")
async def sc_botInfo(interaction: Interaction):
	LOG.LOGGER.debug(f"(command sent) bot-info")
	
	updateGuildData({"commands": [1, "add"]}, interaction.guild.id)
	updateUserData({"commands": [1, "add"]}, interaction.user.id)

	app = await interaction.guild.fetch_member(BOTINFO.ID)

	embed = Embed(color=int(HARIBO.SUCCESS), title="Bot Info", description=BOTINFO.DESCRIPTION)
	embed.set_thumbnail(url=app.display_avatar.url)
	embed.add_field(name="Name", value=f"{app.name}")
	embed.add_field(name="Creator", value=BOTINFO.CREATOR)
	embed.add_field(name="Joined at", value=app.joined_at.strftime("%d.%m.%Y %H:%M"))

	try:
		request = urlopen("https://api.github.com/repos/FabianBartl/HARIBOT/issues?state=all").read()
		issues_list = json.loads(request)
		LOG.LOGGER.debug(f"(successfully requested issues) {issues_list=}")

		labels_dict = dict()
		for issue in issues_list:
			if issue["state"] == "closed":
				labels_dict["Closed"] = labels_dict.get("Closed", 0) + 1
				continue
			for label in issue["labels"]:
				labels_dict[label["name"]] = labels_dict.get(label["name"], 0) + 1
		
		issues_value  = ", ".join([ f"{label}: {labels_dict[label]}" for label in labels_dict ]).title()
		issues_value += f"\n*see: [planned functions](https://github.com/{BOTINFO.REPOSITORY}/issues/20) & [all issues](https://github.com/{BOTINFO.REPOSITORY}/issues)*"
		embed.add_field(name=f"Issue Tracker", value=issues_value, inline=False)
	
	except Exception as e:
		LOG.LOGGER.error(e)

	try:
		request = urlopen("https://api.github.com/repos/FabianBartl/HARIBOT/contributors").read()
		contrib_list = json.loads(request)
		LOG.LOGGER.debug(f"(successfully requested contributors) {contrib_list=}")

		contrib_dict = { contrib["login"]: {"profile": contrib["html_url"], "num": contrib["contributions"]} for contrib in contrib_list }
		contrib_value = ", ".join([ f"[{contrib}]({contrib_dict[contrib]['profile']}): {contrib_dict[contrib]['num']}" for contrib in contrib_dict ])
		embed.add_field(name=f"Contributors", value=contrib_value, inline=False)
	
	except Exception as e:
		LOG.LOGGER.error(e)

	embed.add_field(name="GitHub", value=f"[{BOTINFO.REPOSITORY}](https://github.com/{BOTINFO.REPOSITORY})")
	embed.add_field(name="Invite", value=f"[private invite]({BOTINFO.INVITE})")
	embed.set_footer(text=f"Bot ID: {app.id}")

	await interaction.response.send_message(embed=embed, ephemeral=True)

#-----#

@bot.slash_command(name="auto-role", description="Manage auto roles.", default_member_permissions=Permissions(administrator=True))
async def sc_autoRole(
	interaction: Interaction
	, action: int = SlashOption(required=True, choices={"add": 0, "list": 1, "remove": 2, "clear": 3})
	, _type: int = SlashOption(required=True, choices={"User": 0, "Bot": 1}, name="type")
	, role: Role = SlashOption(required=True, description="Role not relevant if action is list or clear")
):
	guild = interaction.guild
	_type = "bot" if _type == 1 else "user"
	LOG.LOGGER.debug(f"(command sent) auto-role: {action=}, {_type=}, {role=}")
	
	updateGuildData({"commands": [1, "add"]}, interaction.guild.id)
	updateUserData({"commands": [1, "add"]}, interaction.user.id)

	if action == 0: #add
		updateGuildData({f"auto-roles_{_type}": [role.id, "ins"]}, guild.id)
		msg = f"{role.mention} added to the automatic {_type} roles"
		LOG.LOGGER.info(msg)

	elif action == 1: #list
		auto_role_IDs = getGuildData(guild.id).get(f"auto-roles_{_type}")
		if auto_role_IDs:
			msg  = f"all automatic {_type} roles:\n"
			msg += " ".join([ f"{guild.get_role(roleID).mention}" for roleID in auto_role_IDs ])
		else:
			msg = f"no automatic {_type} roles set"

	elif action == 2: #remove
		updateGuildData({f"auto-roles_{_type}": [role.id, "rem"]}, guild.id)
		msg = f"{role.mention} removed from the automatic {_type} roles"
		LOG.LOGGER.info(msg)

	elif action == 3: #clear
		updateGuildData({f"auto-roles_{_type}": [None, "del"]}, guild.id)
		msg = f"automatic {_type} roles cleared"
		LOG.LOGGER.warning(msg)

	await interaction.response.send_message(msg, ephemeral=True)


@bot.slash_command(name="reaction-role", description="Manage reaction roles.")
async def sc_reactionRole(
	interaction: Interaction
	, action: int = SlashOption(required=True, choices={"add": 0, "list": 1, "remove": 2, "clear": 3})
	, messageID: int = SlashOption(required=True, name="messag-id")
	, emoji: int = SlashOption(required=True)
	, role: Role = SlashOption(required=True)
):
	LOG.LOGGER.debug(f"(command sent) reaction-role add: {action=}, {messageID=}, {emoji=}, {role=}")
	
	updateGuildData({"commands": [1, "add"]}, interaction.guild.id)
	updateUserData({"commands": [1, "add"]}, interaction.user.id)

	await interaction.response.send_message(f"`reaction-role`: `{action=}`, `{messageID=}`, `{emoji=}`, `{role}`", ephemeral=CONFIG.EPHEMERAL)

#---------#
# execute #
#---------#

if __name__ == "__main__": bot.run(TOKEN.DISCORD)
