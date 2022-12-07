
# ================= LIBRARIES ========================================================================================

# ------- nextcord lib -------------------------------------------------------

import nextcord
from nextcord.ext.commands import Bot
from nextcord.errors import NotFound
from nextcord import Member, User, Guild, Message, Interaction, SlashOption, File, Embed, Permissions, Role, Reaction, VoiceState
from nextcord import RawReactionActionEvent, ScheduledEvent, ScheduledEventUser

# ------- other libs ---------------------------------------------------------

import time, json, os, sys, logging, requests, random, asyncio, re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.request import urlopen

# ------- own 'libs'  --------------------------------------------------------

from structs import INFO, TOKEN, COLOR, CONFIG, LOG, TEMPLATE
from functions import *

# ================= SETUP ============================================================================================

bot = Bot(
    command_prefix=CONFIG.PREFIX
    , intents=nextcord.Intents.all()
)

colored = (len(sys.argv) >= 2 and sys.argv[1] == "colored")
level = int(sys.argv[2]) if len(sys.argv) >= 3 and sys.argv[2].isdigit() else logging.INFO

setupLogger(colored, level)

# ================= EVENTS ===========================================================================================

# ------- bot (dis)connect, ready, close -------------------------------------

@bot.event
async def on_connect():
    LOG.LOGGER.info("bot connected")

@bot.event
async def on_ready():
    try:
        await bot.sync_all_application_commands()
        LOG.LOGGER.info(f"synced all application commands")
    except Exception as error:
        LOG.LOGGER.error(error)
    LOG.LOGGER.info("bot is ready")

@bot.event
async def on_close():
    LOG.LOGGER.critical("bot was shut down")

@bot.event
async def on_disconnect():
    LOG.LOGGER.warning("bot was disconnected")
    LOG.LOGGER.info("will be reconnected after 5 seconds (now with reconnect flag)")
    await asyncio.sleep(5)
    await bot.connect(reconnect=True)

# ------- member join, remove ------------------------------------------------

@bot.event
async def on_member_join(member: Member):
    guild = member.guild
    _type = "bot" if member.bot else "user"
    LOG.LOGGER.info(f"member ({_type}) joined")

    updateGuildData({"bots" if _type == "bot" else "users": (1, "add"), "xp": [XP.DEFAULT, "add"]}, member.guild.id)
    updateUserData({"leave_timestamp": (None, "del"), "xp": (XP.DEFAULT, "add")}, member.id)

    auto_role_IDs = getGuildData(guild.id).get(f"auto-roles_{_type}")
    roles = [guild.get_role(roleID) for roleID in auto_role_IDs if guild.get_role(roleID) is not None]
    role_mentions = [role.mention for role in roles]
    for role in roles: await member.add_roles(role)
    LOG.LOGGER.info(f"member ({_type}) gets following roles: {' '.join(role_mentions)}")

@bot.event
async def on_member_remove(member: Member):
    _type = "bot" if member.bot else "user"
    LOG.LOGGER.info(f"member ({_type}) removed")
    updateGuildData({f"{_type}s": (1, "sub")}, member.guild.id)
    updateUserData({"leave_timestamp": (time.time(), "set")}, member.id)

# ------- guild join, remove -------------------------------------------------

@bot.event
async def on_guild_join(guild: Guild):
    LOG.LOGGER.info("guild joined")

    bots, users = 0, 0
    for member in guild.members:
        if member.bot: bots  += 1
        else:          users += 1
    
    updateGuildData({
        "bots": (bots, "add")
        , "users": (users, "add")
        , "leave_timestamp": (None, "del")
    }, guild.id)

@bot.event
async def on_guild_remove(guild: Guild):
    LOG.LOGGER.info("guild removed")
    updateGuildData({"leave_timestamp": (time.time(), "set")}, guild.id)

# ------- reaction add, remove, clear (emoji) --------------------------------

@bot.event
async def on_raw_reaction_add(payload: RawReactionActionEvent):
    LOG.LOGGER.debug(f"on_raw_reaction_add")
    if payload.member is None: return

    guild = payload.member.guild
    channel = await guild.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    member = payload.member
    emoji = payload.emoji
    LOG.LOGGER.debug(f"(reaction added) {message.id}: '{member.display_name}: {emoji}'")
    LOG.LOGGER.debug(f"(added received reaction) {message.author.display_name} <- {member.display_name}: '{emoji}'")

    updateGuildData({"reactions_given": (1, "add")}, guild.id)
    updateUserData({"reactions_given": (1, "add")}, member.id)
    updateUserData({"reactions_received": (1, "add")}, message.author.id)

@bot.event
async def on_raw_reaction_remove(payload: RawReactionActionEvent):
    LOG.LOGGER.debug(f"on_raw_reaction_remove")
    guild = await bot.fetch_guild(payload.guild_id)
    if guild is None: return

    channel = await guild.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    member = await guild.fetch_member(payload.user_id)
    emoji = payload.emoji
    LOG.LOGGER.debug(f"(reaction removed) {message.id}: '{member.display_name}: {emoji}'")
    LOG.LOGGER.debug(f"(removed received reaction) {message.author.display_name} <- {member.display_name}: '{emoji}'")

    updateGuildData({"reactions_given": (1, "sub")}, guild.id)
    updateUserData({"reactions_given": (1, "sub")}, member.id)
    updateUserData({"reactions_received": (1, "sub")}, message.author.id)

@bot.event
async def on_reaction_clear(message: Message, reactions_given: list[Reaction,]):
    emojis = f"{reactions_given.message.author.display_name}:\n"
    emojis += ", ".join([f"`{reaction.emoji}`" for reaction in reactions_given])
    LOG.LOGGER.debug(f"(reaction cleared) {message.id}: '{emojis}'")

@bot.event
async def on_reaction_clear_emoji(reaction: Reaction):
    user = reaction.message.author
    message = reaction.message
    emoji = reaction.emoji
    LOG.LOGGER.debug(f"(reaction cleared emoji) {message.id}: '{user.display_name}: {emoji}'")

# ------- message sent, edit, delete -----------------------------------------

@bot.event
async def on_message(message: Message):
    attachments = message.attachments
    content     = message.content
    channel     = message.channel
    author      = message.author
    guild       = message.guild
    LOG.LOGGER.debug(f"(msg sent) {channel.name} - {author.display_name}: {f'({len(attachments)} Attachments)' if len(attachments) > 0 else ''} '{content}'")

    words = len(re.sub(" +", " ", content).split(" "))
    letters = len(content)
    last_message = time.time()

    user_data = getUserData(author.id)
    last_message_before = user_data.get("last_message", 0)
    xp = user_data.get("xp", 0)

    xp += XP.DEFAULT if xp < XP.DEFAULT else 0
    xp += XP.GENERATE(last_message_before, last_message) if author.id != INFO.BOT.ID else XP.RANGE_MULTIPLIER
    LOG.LOGGER.debug(f"(xp earned) {author.display_name}: {xp}")

    updateGuildData({
        "messages": (1, "add")
        , "words": (words, "add")
        , "letters": (letters, "add")
        , "attachments": (len(attachments), "add")
        , "xp": (xp, "set")
    }, guild.id)
    updateUserData({
        "messages": (1, "add")
        , "words": (words, "add")
        , "letters": (letters, "add")
        , "attachments": (len(attachments), "add")
        , "xp": (xp, "set")
        , "last_message": (last_message, "set" if XP.COOLDOWN_ELAPSED(last_message_before, last_message) else "ign")
    }, author.id)

    await resolve_command(message)

@bot.event
async def on_message_edit(before: Message, after: Message):
    author = before.author
    guild  = before.guild
    LOG.LOGGER.debug(f"(msg edits before) {before.channel.name} - {before.author.display_name}: '{before.content}'")
    LOG.LOGGER.debug(f"(msg edits after)  {after.channel.name} - {after.author.display_name}: '{after.content}'")

    changes = abs(len(after.content) - len(before.content))
    attachments = len(after.attachments) - len(before.attachments)
    words = len(re.sub(" +", " ", after.content).split(" ")) - len(re.sub(" +", " ", before.content).split(" "))
    letters = len(after.content) - len(before.content)

    updateGuildData({
        "edits": (1, "add")
        , "changes_lenght": (changes, "add")
        , "words": (words, "add")
        , "letters": (letters, "add")
        , "attachments": (attachments, "add")
    }, guild.id)
    updateUserData({
        "edits": (1, "add")
        , "changes_lenght": (changes, "add")
        , "words": (words, "add")
        , "letters": (letters, "add")
        , "attachments": (attachments, "add")
    }, author.id)

@bot.event
async def on_message_delete(message: Message):
    author  = message.author
    guild   = message.guild
    content = message.content
    LOG.LOGGER.debug(f"(msg deleted) {message.channel.name} - {message.author.display_name}: '{message.content}'")

    attachments = len(message.attachments)
    words = len(re.sub(" +", " ", content).split(" "))
    letters = len(content)

    updateGuildData({
        "deleted": (1, "add")
        , "words": (words, "sub")
        , "letters": (letters, "sub")
        , "attachments": (attachments, "sub")
    }, guild.id)
    updateUserData({
        "deleted": (1, "add")
        , "words": (words, "sub")
        , "letters": (letters, "sub")
        , "attachments": (attachments, "sub")
    }, author.id)

# ------- scheduled event create, delete, update, user add, user remove ------

@bot.event
async def on_guild_scheduled_event_create(_event: ScheduledEvent):
    event = await _event.guild.fetch_scheduled_event(_event.id)

    name    = event.name
    creator = event.creator
    guild   = event.guild
    LOG.LOGGER.warning(f"(scheduled event) `{name}` created by {creator.display_name}")

    updateGuildData({"events_created": (1, "add")}, guild.id)
    updateUserData({"events_created": (1, "add")}, creator.id)

    roleName = TEMPLATE.EVENT_ROLENAME(event_name=event.name, event_id=event.id)
    await guild.create_role(name=roleName, reason=f"event {event.id} created", mentionable=True)

@bot.event
async def on_guild_scheduled_event_delete(event: ScheduledEvent):
    name  = event.name
    guild = event.guild
    LOG.LOGGER.warning(f"(scheduled event) `{name}` deleted")

    updateGuildData({"events_deleted": (1, "add")}, guild.id)
    
    roleName = TEMPLATE.EVENT_ROLENAME(event_name=event.name, event_id=event.id)
    roles = await guild.fetch_roles()
    if role := findRole(roleName, roles): await role.delete(reason=f"event {event.id} deleted")

@bot.event
async def on_guild_scheduled_event_update(before: ScheduledEvent, after: ScheduledEvent):
    guild = before.guild
    LOG.LOGGER.warning(f"(scheduled event) `{after.name}` updated")

    updateGuildData({"events_updated": (1, "add")}, guild.id)
    
    roleNameBefore = TEMPLATE.EVENT_ROLENAME(event_name=before.name, event_id=before.id)
    roleNameAfter = TEMPLATE.EVENT_ROLENAME(event_name=after.name, event_id=after.id)
    roles = await guild.fetch_roles()
    if role := findRole(roleNameBefore, roles): await role.edit(name=roleNameAfter, reason=f"event `{after.id}` updated")
    else: await guild.create_role(name=roleNameAfter, reason=f"event `{before.id}` updated", mentionable=True)

@bot.event
async def on_guild_scheduled_event_user_add(event: ScheduledEvent, eventUser: ScheduledEventUser):
    user  = eventUser.user
    name  = event.name
    guild = event.guild
    LOG.LOGGER.warning(f"(scheduled event) {user.display_name} interested in `{name}`")

    updateGuildData({"events_interested": (1, "add")}, guild.id)
    updateUserData({"events_interested": (1, "add")}, user.id)

    roleName = TEMPLATE.EVENT_ROLENAME(event_name=event.name, event_id=event.id)
    member = await guild.fetch_member(user.id)
    roles = await guild.fetch_roles()
    if role := findRole(roleName, roles): await member.add_roles(role, reason=f"interested in event `{event.id}`")
    else: await guild.create_role(name=roleName, reason=f"event `{event.id}` created", mentionable=True)

@bot.event
async def on_guild_scheduled_event_user_remove(event: ScheduledEvent, eventUser: ScheduledEventUser):
    user  = eventUser.user
    name  = event.name
    guild = event.guild
    LOG.LOGGER.warning(f"(scheduled event) {user.display_name} uninterested in `{name}`")

    updateGuildData({"events_interested": (1, "sub")}, guild.id)
    updateUserData({"events_interested": (1, "sub")}, user.id)

    roleName = TEMPLATE.EVENT_ROLENAME(event_name=event.name, event_id=event.id)
    member = await guild.fetch_member(user.id)
    roles = await guild.fetch_roles()
    if role := findRole(roleName, roles): await member.remove_roles(role, reason=f"uninterested in event `{event.id}`")

# ------- role create, delete, update ----------------------------------------

@bot.event
async def on_guild_role_create(role: Role):
    LOG.LOGGER.debug(f"role '{role.name}' created")

@bot.event
async def on_guild_role_delete(role: Role):
    LOG.LOGGER.debug(f"role '{role.name}' deleted")

@bot.event
async def on_guild_role_update(before: Role, after: Role):
    pass

# ------- presence, user, voice state update ---------------------------------

@bot.event
async def on_presence_update(before: Member, after: Member):
    pass

@bot.event
async def on_user_update(before: User, after: User):
    pass

@bot.event
async def on_voice_state_update(member: Member, before: VoiceState, after: VoiceState):
    pass

# ================= SLASH COMMANDS ===================================================================================

# ------- help ---------------------------------------------------------------

@bot.slash_command(name="help", description="Overview of all commands.")
async def sc_help(interaction: Interaction):
    LOG.LOGGER.debug(f"(slash command sent) help")

    updateGuildData({"commands": (1, "add")}, interaction.guild.id)
    updateUserData({"commands": (1, "add")}, interaction.user.id)

    commands = bot.get_all_application_commands()
    commands = sorted(commands, key=lambda x: x.qualified_name)

    embed = Embed(color=int(COLOR.HARIBO.INFO), title="Command Overview")
    for command in commands:
        embed.add_field(name=f"`/{command.qualified_name}`", value=command.description)

    await interaction.response.send_message(embed=embed, ephemeral=True)

# ------- test ---------------------------------------------------------------

@bot.slash_command(name="test", description="Test some new stuff.", default_member_permissions=Permissions(administrator=True))
async def sc_test(interaction: Interaction):
    LOG.LOGGER.debug(f"(slash command sent) test")

    updateGuildData({"commands": (1, "add")}, interaction.guild.id)
    updateUserData({"commands": (1, "add")}, interaction.user.id)

    endDate = (datetime.today() + timedelta(weeks=4)).strftime(r"%Y-%m-%d")
    url = f"https://api.teamup.com/{INFO.SERVER.TEAMUP}/events"
    headers = {"Teamup-Token": TOKEN.TEAMUP}
    params = {"format": "markdown", "endDate": endDate}
    response = requests.get(url, headers=headers, params=params)
    LOG.LOGGER.warning(response.text)

    response_dict = response.json()
    msg_lines = [ f"**{event['title']}** at *{event['start_dt']}* by {event['who']}" for event in response_dict.get("events", []) ]

    await interaction.response.send_message("\n".join(msg_lines), ephemeral=True)

# ------- log ----------------------------------------------------------------

@bot.slash_command(name="log", description="Manage logging files.", default_member_permissions=Permissions(administrator=True))
async def sc_log(
        interaction: Interaction
        , action: int = SlashOption(required=True, choices={"backup": 0, "save": 1, "get": 2, "clear": 3, "reset": 4, "list": 5})
):
    LOG.LOGGER.debug(f"(slash command sent) log: {action=}")

    updateGuildData({"commands": (1, "add")}, interaction.guild.id)
    updateUserData({"commands": (1, "add")}, interaction.user.id)

    dstFile = f"log_{datetime.today().strftime(r'%Y-%m-%d_%H-%M-%S')}.dat"
    dstPath = os.path.abspath(os.path.join(LOG.DIR, dstFile))

    response_kwargs = dict()

    if action == 0: # backup: save, get, clear
        name = "Backup current log: *save - get - clear*"
        color = COLOR.HARIBO.SUCCESS
        log_code, dstSize = backupLogFile(dstPath)
        value = f"log of size `{formatBytes(dstSize)}` backuped as `{dstFile}`"
        response_kwargs["file"] = File(dstPath, filename=dstFile)

    elif action == 1: # save
        name = "Save current log"
        color = COLOR.HARIBO.SUCCESS
        dstSize = saveLogFile(dstPath)
        value = f"log of size `{formatBytes(dstSize)}` saved as `{dstFile}`"

    elif action == 2: # get
        name = "Get last lines of current log"
        color = COLOR.HARIBO.INFO
        log_code = getLogFile(max_chars=1020).replace("`", "'")
        value = f"```cmd\n...\n{log_code}\n```"
        response_kwargs["file"] = File(LOG.PATH, filename=dstFile)

    elif action == 3: # clear
        name = "Clear current log"
        if checkOwner(interaction.user.id):
            color = COLOR.HARIBO.WARNING
            clearLogFile()
            value = f"log file cleared"
        else:
            color = COLOR.HARIBO.DANGER
            value = f"no permission to use"

    elif action == 4: # reset
        name = "Reset complete log"
        if checkOwner(interaction.user.id):
            color = COLOR.HARIBO.WARNING
            logFiles = resetLogFiles()
            value = f"all {len(logFiles)} log file(s) deleted / cleared"
        else:
            color = COLOR.HARIBO.DANGER
            value = f"no permission to use"

    elif action == 5: # list
        name = "List all log files"
        color = COLOR.HARIBO.INFO
        logFiles = os.scandir(LOG.DIR)
        value = "```cmd\n" + "\n".join([ f"{formatBytes(file.stat().st_size):>10} | {file.name}" for file in logFiles ]) + "\n```"

    response_kwargs["embed"] = Embed(color=int(color), title="Logging Manager")
    response_kwargs["embed"].add_field(name=name, value=value)

    await interaction.response.send_message(**response_kwargs, ephemeral=True)

# ------- ping ---------------------------------------------------------------

@bot.slash_command(name="ping", description="Test bot response.")
async def sc_ping(interaction: Interaction):
    LOG.LOGGER.debug(f"(slash command sent) ping")

    updateGuildData({"commands": (1, "add")}, interaction.guild.id)
    updateUserData({"commands": (1, "add")}, interaction.user.id)

    latency = bot.latency
    msg = f"`{latency * 1000:.0f} ms` latency"
    if   latency > 400: LOG.LOGGER.warning(msg)
    elif latency > 900: LOG.LOGGER.critical(msg)

    await interaction.response.send_message(f"pong with {msg}", ephemeral=True)

# ------- score --------------------------------------------------------------

@bot.slash_command(name="score", description="Get the score of a mentioned member.")
async def sc_score(
        interaction: Interaction
        , member: Member = SlashOption(required=False)
        , formatID: int = SlashOption(required=False, choices={"SVG": 0, "PNG": 1}, default=1, name="format")
        , private: bool = SlashOption(required=False, default=CONFIG.EPHEMERAL)
):
    LOG.LOGGER.debug(f"(slash command sent) score: {member=}")

    updateGuildData({"commands": (1, "add")}, interaction.guild.id)
    updateUserData({"commands": (1, "add")}, interaction.user.id)

    if type(member) is not Member: member = interaction.user
    formats = ["svg", "png"]
    format = formats[formatID]

    await interaction.response.defer(ephemeral=private)
    score_card_file_func = createScoreCard(member)
    await interaction.followup.send(file=File(score_card_file_func(format)), ephemeral=private)
    
    await asyncio.sleep(1)
    for format in formats: os.remove(score_card_file_func(format))
    LOG.LOGGER.warning(f"deleted temp score card files `{score_card_file_func('*')}`")

# ------- member, server, bot info -------------------------------------------

@bot.slash_command(name="member-info", description="Get information about a mentioned member.")
async def sc_memberInfo(
        interaction: Interaction
        , member: Member = SlashOption(required=False)
):
    LOG.LOGGER.debug(f"(slash command sent) member-info: {member=}")

    updateGuildData({"commands": (1, "add")}, interaction.guild.id)
    updateUserData({"commands": (1, "add")}, interaction.user.id)

    if type(member) is not Member: member = interaction.user
    userData = getUserData(member.id)

    embed = Embed(color=int(COLOR.HARIBO.SUCCESS), title="Member Info")
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Username", value=f"{member.name}#{member.discriminator}")
    embed.add_field(name="Nickname", value=member.display_name)
    embed.add_field(name="Is a Bot", value="Yes" if member.bot else "No")

    embed.add_field(name="Joined at", value=member.joined_at.strftime(r"%d.%m.%Y %H:%M"))
    embed.add_field(name="Messages", value=userData.get("messages", 0))
    embed.add_field(name="Words/Message", value=round(userData.get("words", 0) / userData.get("messages", 1), 2))

    embed.add_field(name="Roles", value=" ".join([role.mention for role in member.roles[1:]]), inline=False)
    embed.add_field(name="PGP-Emails", value=", ".join(userData.get("emails", ["*no emails deposited*"])), inline=False)
    embed.set_footer(text=f"Member ID: {member.id}")

    await interaction.response.send_message(embed=embed, ephemeral=CONFIG.EPHEMERAL)

@bot.slash_command(name="server-info", description="Get information about this server.")
async def sc_serverInfo(interaction: Interaction):
    LOG.LOGGER.debug(f"(slash command sent) server-info")

    updateGuildData({"commands": (1, "add")}, interaction.guild.id)
    updateUserData({"commands": (1, "add")}, interaction.user.id)

    guild = interaction.guild
    guildData = getGuildData(guild.id)

    embed = Embed(color=int(COLOR.HARIBO.SUCCESS), title="Server Info", description=guild.description)
    embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="Name", value=guild.name, inline=False)

    embed.add_field(name="Users", value=guildData.get("users", 0))
    embed.add_field(name="Bots", value=guildData.get("bots", 0))
    embed.add_field(name="Messages", value=guildData.get("messages", 0))

    embed.add_field(name="Event Overview", value=f"[Teamup Calender](https://teamup.com/{INFO.SERVER.TEAMUP})", inline=False)
    embed.add_field(name="Invite", value=f"[open](https://discord.gg/{INFO.SERVER.INVITE}) or copy invite:\n```\nhttps://discord.gg/{INFO.SERVER.INVITE}\n```", inline=False)
    embed.set_footer(text=f"Server ID: {guild.id}")

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.slash_command(name="bot-info", description="Get information about this bot.")
async def sc_botInfo(interaction: Interaction):
    LOG.LOGGER.debug(f"(slash command sent) bot-info")

    updateGuildData({"commands": (1, "add")}, interaction.guild.id)
    updateUserData({"commands": (1, "add")}, interaction.user.id)

    app = await interaction.guild.fetch_member(INFO.BOT.ID)

    embed = Embed(color=int(COLOR.HARIBO.SUCCESS), title="Bot Info", description=INFO.BOT.DESCRIPTION)
    embed.set_thumbnail(url=app.display_avatar.url)
    embed.add_field(name="Name", value=app.name)
    embed.add_field(name="Creator", value=INFO.BOT.CREATOR)
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

        issues_value = ", ".join([f"{label}: {labels_dict[label]}" for label in labels_dict]).title()
        issues_value += f"\n*see: [planned functions](https://github.com/{INFO.BOT.REPOSITORY}/issues/20) & [all issues](https://github.com/{INFO.BOT.REPOSITORY}/issues)*"
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

    embed.add_field(name="GitHub", value=f"[{INFO.BOT.REPOSITORY}](https://github.com/{INFO.BOT.REPOSITORY})")
    embed.add_field(name="Invite", value=f"[private invite]({INFO.BOT.INVITE})")
    embed.set_footer(text=f"Bot ID: {app.id}")

    await interaction.response.send_message(embed=embed, ephemeral=True)

# ------- auto, reaction role ------------------------------------------------

@bot.slash_command(name="auto-role", description="Manage auto roles.", default_member_permissions=Permissions(administrator=True))
async def sc_autoRole(
        interaction: Interaction
        , action: int = SlashOption(required=True, choices={"add": 0, "list": 1, "remove": 2, "clear": 3})
        , _type: int = SlashOption(required=True, choices={"User": 0, "Bot": 1}, name="type")
        , role: Role = SlashOption(required=True, description="Role not relevant if action is list or clear")
):
    guild = interaction.guild
    _type = "bot" if _type == 1 else "user"
    LOG.LOGGER.debug(f"(slash command sent) auto-role: {action=}, {_type=}, {role=}")

    updateGuildData({"commands": (1, "add")}, interaction.guild.id)
    updateUserData({"commands": (1, "add")}, interaction.user.id)

    if action == 0: # add
        updateGuildData({f"auto-roles_{_type}": [role.id, "ins"]}, guild.id)
        msg = f"{role.mention} added to the automatic {_type} roles"
        LOG.LOGGER.info(msg)

    elif action == 1: # list
        auto_role_IDs = getGuildData(guild.id).get(f"auto-roles_{_type}")
        if auto_role_IDs:
            msg = f"all automatic {_type} roles:\n"
            msg += " ".join([f"{guild.get_role(roleID).mention}" for roleID in auto_role_IDs])
        else:
            msg = f"no automatic {_type} roles set"

    elif action == 2: # remove
        updateGuildData({f"auto-roles_{_type}": [role.id, "rem"]}, guild.id)
        msg = f"{role.mention} removed from the automatic {_type} roles"
        LOG.LOGGER.info(msg)

    elif action == 3: # clear
        updateGuildData({f"auto-roles_{_type}": [None, "del"]}, guild.id)
        msg = f"automatic {_type} roles cleared"
        LOG.LOGGER.warning(msg)

    await interaction.response.send_message(msg, ephemeral=True)

@bot.slash_command(name="reaction-role", description="Manage reaction roles.", default_member_permissions=Permissions(administrator=True))
async def sc_reactionRole(
        interaction: Interaction
        , action: int = SlashOption(required=True, choices={"add": 0, "list": 1, "remove": 2, "clear": 3})
        , messageID: int = SlashOption(required=True, name="message-id")
        , emoji: int = SlashOption(required=True)
        , role: Role = SlashOption(required=True)
):
    LOG.LOGGER.debug(f"(slash command sent) reaction-role add: {action=}, {messageID=}, {emoji=}, {role=}")

    updateGuildData({"commands": (1, "add")}, interaction.guild.id)
    updateUserData({"commands": (1, "add")}, interaction.user.id)

    await interaction.response.send_message(f"`reaction-role`: `{action=}`, `{messageID=}`, `{emoji=}`, `{role}`", ephemeral=CONFIG.EPHEMERAL)

# ------- what-if ------------------------------------------------------------

@bot.slash_command(name="what-if", description="Returns a random *WHAT IF?* image.")
async def sc_whatIf(
        interaction: Interaction
        , num: int = SlashOption(required=False, default=-1)
):
    LOG.LOGGER.debug(f"(slash command sent) what-if: {num=}")

    updateGuildData({"commands": (1, "add")}, interaction.guild.id)
    updateUserData({"commands": (1, "add")}, interaction.user.id)

    htmlDoc = BeautifulSoup(requests.get("https://xkcd.com/archive/").text, "html.parser")
    image_count = int(htmlDoc.select_one("#middleContainer > a:nth-child(5)")["href"][1:-1])
    LOG.LOGGER.debug(f"{image_count=}, {htmlDoc=}")

    num = random.randint(0, image_count) if num < 0 else image_count

    htmlDoc = BeautifulSoup(requests.get(f"https://xkcd.com/{num}/").text, "html.parser")
    image_title = htmlDoc.select_one("#ctitle").text
    image_url = htmlDoc.select_one("#middleContainer > a:nth-child(8)")["href"]
    LOG.LOGGER.debug(f"{image_title=}, {image_url=}, {htmlDoc=}")

    await interaction.response.send_message(f"**{image_title}** *(image {num})*\n{image_url}", ephemeral=CONFIG.EPHEMERAL)

# ------- pgp set (help), get, delete ----------------------------------------

@bot.slash_command(name="pgp-set", description=f"Just the help to set a pgp-key with `{CONFIG.PREFIX}pgp-set`.")
async def sc_pgpSet(interaction: Interaction):
    LOG.LOGGER.debug(f"(slash command sent) pgp-set")
    
    embed = Embed(color=int(COLOR.HARIBO.INFO), title=f"Help for `{CONFIG.PREFIX}pgp-set [email]`")
    embed.add_field(name="`[email]`", value="The corresponding email to the pgp-key.", inline=False)
    embed.add_field(name="`[keyfile]`", value="The pgp-keyfile as message attachment.", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.slash_command(name="pgp-get", description="Returns the pgp-key to the given email address.")
async def sc_pgpGet(interaction: Interaction, email: str=SlashOption(required=True)):
    LOG.LOGGER.debug(f"(slash command sent) pgp-get: {email=}")
    
    response_kwargs = dict()
    pgp_path = os.path.abspath(os.path.join(DIR.PGP, f"{email}.asc"))

    if not os.path.isfile(pgp_path):
        response_kwargs["embed"] = Embed(color=int(COLOR.HARIBO.WARNING), title=f"For the given email address `{email}`, no pgp-key is known.")
    else:
        response_kwargs["content"] = f"PGP-Key for `{email}`:"
        response_kwargs["file"] = File(pgp_path)

    await interaction.response.send_message(**response_kwargs, ephemeral=CONFIG.EPHEMERAL)

@bot.slash_command(name="pgp-delete", description="Deletes the given email and it's pgp-key out of your user data.")
async def sc_pgpDelete(interaction: Interaction, email: str = SlashOption(required=True)):
    userID   = interaction.user.id
    userData = getUserData(userID)
    LOG.LOGGER.debug(f"(slash command sent) pgp-delete: {email=}")

    emails = set(userData.get("emails", []))
    if email not in emails:
        embed = Embed(color=int(COLOR.HARIBO.WARNING), title=f"You are not allowed to delete this email.")
        await interaction.response.send_message(embed=embed)
        return

    pgp_path = os.path.abspath(os.path.join(DIR.PGP, f"{email}.asc"))

    if not os.path.isfile(pgp_path):
        embed = Embed(color=int(COLOR.HARIBO.WARNING), title=f"For the given email address no pgp-key is known.")
        await interaction.response.send_message(embed=embed)
        return

    os.remove(pgp_path)
    updateUserData({"emails": (email, "rem")}, userID)
    await interaction.response.send_message(f"Your email `{email}` and the corresponding pgp-key were deleted from your user data.", ephemeral=CONFIG.EPHEMERAL)

# ================= COMMANDS =========================================================================================

# ------- pgp set ------------------------------------------------------------

async def mc_pgpSet(message: Message):
    attachments  = message.attachments
    channel      = message.channel
    command_args = re.sub(r" +", " ", message.content).split(" ")
    LOG.LOGGER.debug(f"(message command sent) pgp-set: {command_args=}")

    error_message = False
    error_ttl = 10

    if len(command_args) < 2:
        embed = Embed(color=int(COLOR.HARIBO.WARNING), title="no email given")
        await channel.send(embed=embed, delete_after=error_ttl)
        return

    regex_email = re.compile(r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+")
    email = command_args[1]
    if not re.fullmatch(regex_email, email):
        error_message = "Invalid email."
    elif not len(attachments) == 1:
        error_message = "Please attach one file only."
    elif os.path.isfile(os.path.join(DIR.PGP, f"{email}.asc")):
        error_message = "This email is already registered."

    if error_message:
        embed = Embed(color=int(COLOR.HARIBO.WARNING), title=error_message)
        await channel.send(embed=embed, delete_after=error_ttl)
        return

    keyfile_attachment = attachments[0]
    if not keyfile_attachment.content_type.startswith("text"):
        embed = Embed(color=int(COLOR.HARIBO.WARNING), title="The keyfile must be of the `text` content type.")
        await channel.send(embed=embed, delete_after=error_ttl)
        return

    keyfile = requests.get(keyfile_attachment.url)
    pgp_key = keyfile.content.decode("ascii")
    if pgp_key.startswith("-----BEGIN PGP PRIVATE KEY BLOCK-----"):
        LOG.LOGGER.warning(f"{message.author.display_name} uploaded a private pgp-key")
        error_message = "YOU ARE AN IDIOT. YOU UPLOADED YOUR PRIVATE KEY.\nIMMEDIATELY DEPRECATE AND REVOKE THIS KEY AND CREATE A NEW PAIR."
        color = COLOR.HARIBO.DANGER
    elif not pgp_key.startswith("-----BEGIN PGP PUBLIC KEY BLOCK-----"):
        error_message = "The attachment must be a public pgp-key."
        color = COLOR.HARIBO.WARNING
    
    if error_message:
        embed = Embed(color=int(color), title=error_message)
        await channel.send(embed=embed, delete_after=error_ttl)
        return
    
    updateUserData({"emails": (email, "ins")}, message.author.id)
    with open(os.path.join(DIR.PGP, f"{email}.asc"), "w+") as fobj: fobj.write(pgp_key)

    embed = Embed(color=int(COLOR.HARIBO.SUCCESS), title="Your pgp-key is stored successfully.")
    await channel.send(embed=embed, delete_after=error_ttl)

# ================= FUNCTIONS ========================================================================================

async def resolve_command(message: Message):
    prefix  = CONFIG.PREFIX
    content = message.content

    if content.startswith(f"{prefix}pgp-set"): await mc_pgpSet(message)

# ================= EXECUTE ==========================================================================================

if __name__ == "__main__": bot.run(TOKEN.DISCORD)
