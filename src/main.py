
# define and parse cli arguments
import argparse
import logging

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--log-level", type=int, default=logging.INFO, help="The minimal logging level")
parser.add_argument("-nc", "--no-color", action="store_true", help="No colored console output")
ARGS = parser.parse_args()

# setup custom logger
import os
from datetime import datetime, timedelta
import custom_logger as clog

log_level = ARGS.log_level
log_file = "{time}_{name}.log".format(time=datetime.strftime(datetime.now(), "%Y-%m-%d_%H-%M-%S"), name=os.path.basename(__file__))
log_path = os.path.join("logs", log_file)
log_color = not ARGS.no_color
clog.setBasicConfig(log_level, "%(asctime)s | %(levelname)8s | %(message)s", "%Y-%m-%d %H:%M:%S", log_path, use_color=log_color)
LOGGER = clog.getLogger()

# open database connection
import sqlite3
db_path = os.path.join("data", "haribot-db.db")
DBCONN = sqlite3.connect(db_path)
DBCURSER = DBCONN.cursor()

import sys
import json
from pprint import pprint
from typing import Optional

import nextcord
from nextcord import ScheduledEvent, ScheduledEventUser
from nextcord import Interaction, VoiceState, VoiceChannel
from nextcord import Member, User, Role, Intents, Permissions
from nextcord import SlashOption
from nextcord.ext.commands import Bot

# setup the nextcoord bot and load outsourced functions
from custom_functions import *
BOT = Bot(intents=Intents.all())


class Group__before_and_after_connection:
    @BOT.event
    async def on_connect():
        global LOGGER
        LOGGER.info("bot connected")

    @BOT.event
    async def on_ready():
        global BOT, LOGGER
        LOGGER.info(f"bot logged in as {BOT.user}")
        await BOT.sync_all_application_commands()
        clog.debug("commands synced")
            
    @BOT.event
    async def on_close():
        global LOGGER, DBCONN
        DBCONN.close()
        LOGGER.warning("bot shut down, database connection closed")

    @BOT.event
    async def on_disconnect():
        global LOGGER
        LOGGER.warning("bot disconnected")


"""
TODO:
 - add more logging info
"""
class Group__scheduled_event_role_management:
    @BOT.event
    async def on_guild_scheduled_event_create(event: ScheduledEvent):
        global LOGGER, DBCURSER
        """
        - create role for scheduled event containing name and id
        - store the event in the local database
        - add event to calender by @noeppi-noeppi
        """
        LOGGER.info(f"event {event} created")
        # create role
        event_role = await event.guild.create_role(name=create_event_role_name(event), reason=f"event {event} created", mentionable=True)
        # store event and role in database
        DiscordEvent(DBCONN).insert(event, event_role)
        # TODO: calender integration

    @BOT.event
    async def on_guild_scheduled_event_delete(event: ScheduledEvent):
        global LOGGER
        """
        - find the associated scheduled event role and delete it
        - database: set discord event status to cancelled
        """
        LOGGER.info(f"event {event} deleted")
        if event_role := get_role_for_event(event):
            await event_role.delete(reason=f"event {event} deleted")
        DiscordEvent(DBCONN).update_many(event.id, {"status": "deleted", "notifier_role": None})

    @BOT.event
    async def on_guild_scheduled_event_update(event_before: ScheduledEvent, event_after: ScheduledEvent):
        global LOGGER
        # on: scheduled event name update
        if event_before.name != event_after.name:
            """
            - find the associated scheduled event role and update its name
            """
            LOGGER.info(f"event {event_before} updated to {event_after}")
            if event_after_role := get_role_for_event(event_after):
                await event_after_role.edit(name=create_event_role_name(event_after), reason=f"event {event_after} updated")
        # TODO: update database entry
        discord_event_before = DiscordEvent(DBCONN).select_all(event_before.id)

    @BOT.event
    async def on_guild_scheduled_event_user_add(event: ScheduledEvent, user: ScheduledEventUser):
        """
        - give interested user the associated role
        """
        if event_role := get_role_for_event(event):
            if member := event.guild.get_member(user.id):
                await member.add_roles(event_role, reason=f"interested in event {event}")

    @BOT.event
    async def on_guild_scheduled_event_user_remove(event: ScheduledEvent, user: ScheduledEventUser):
        """
        - remove associated role from uninterested user
        """
        if event_role := get_role_for_event(event):
            if member := event.guild.get_member(user.id):
                await member.remove_roles(event_role, reason=f"uninterested in event {event}")

    @BOT.event
    async def on_voice_state_update(member: Member, state_before: VoiceState, state_after: VoiceState):
        # on: member joins voice/stage channel
        if not state_before.channel and state_after.channel:
            """
            - update scheduled event state
            """
            planned_events = get_events_for_voice_channel(state_after.channel)
            for event in planned_events:
                await update_scheduled_event_state(event)
        
        # on: member leaves voice/stage channel
        elif state_before.channel and not state_after.channel:
            """
            - update scheduled event state
            """
            planned_events = get_events_for_voice_channel(state_before.channel)
            for event in planned_events:
                await update_scheduled_event_state(event)
        
        # on: e.g. member is muted/unmuted
        else:
            pass


class Group__slash_commands:
    @BOT.slash_command(name="ping", description="Get latency")
    async def sc_ping(interaction: Interaction):
        global BOT, LOGGER
        LOGGER.info("slash command used: /ping")
        await interaction.send(f"pong with {int(BOT.latency*1000)} ms latency")
    
    @BOT.slash_command(name="test", description="Temporary command to test specific something", default_member_permissions=Permissions(8))
    async def sc_test(interaction: Interaction):
        global BOT, LOGGER
        LOGGER.info("slash command used: /test")
        
        var = DiscordEvent().fetch_from_database(1299067248828485653, DBCONN)
        print(var, type(var))
        
        await interaction.send(f"pong with {int(BOT.latency*1000)} ms latency")
    
    @BOT.slash_command(name="create-test-event", description="Create an scheduled event for testing purposes", default_member_permissions=Permissions(8))
    async def sc_create_test_event(interaction: Interaction):
        event = await interaction.guild.create_scheduled_event(
            entity_type=nextcord.ScheduledEventEntityType.voice,
            name=f"Test Event [{int(datetime.now().timestamp())}]",
            description="Lorem Ipsum dolor sit amet.",
            start_time=datetime.now(),
            channel=interaction.guild.get_channel(1023618467171139674),
            reason="Event for testing purposes"
        )
        await interaction.send(f"event {event} created")

    @BOT.slash_command(name="clear-test-events", description="Delete all test events", default_member_permissions=Permissions(8))
    async def sc_clear_test_events(interaction: Interaction):
        message = ""
        for event in interaction.guild.scheduled_events:
            if event.name.startswith("Test Event ["):
                await interaction.guild.get_scheduled_event(event.id).delete()
                message += f"event {event} deleted\n"
        await interaction.send(message)


# get tokens and start bot
with open("tokens.json", "r", encoding="utf-8") as file:
    TOKENS = json.load(file)
BOT.run(TOKENS["discord"])
