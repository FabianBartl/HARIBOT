
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
import time
from pprint import pprint, pformat
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
    @staticmethod
    @BOT.event
    async def on_connect():
        clog.info("bot connected")

    @staticmethod
    @BOT.event
    async def on_ready():
        global BOT
        clog.info("bot logged in as %s", BOT.user)
        await BOT.sync_all_application_commands()
        clog.debug("commands synced")
            
    @staticmethod
    @BOT.event
    async def on_close():
        global DBCONN
        DBCONN.close()
        clog.warning("bot shut down, database connection closed")

    @staticmethod
    @BOT.event
    async def on_disconnect():
        clog.warning("bot disconnected")



class Group__scheduled_event_role_management:
    @staticmethod
    @BOT.event
    async def on_guild_scheduled_event_create(event: ScheduledEvent) -> None:
        global DBCURSER
        clog.info("event %s created", event)
        """
        - create role for scheduled event containing name and id
        - store the event in the local database
        - add event to calender by @noeppi-noeppi
        """
        # create role
        event_role = await event.guild.create_role(name=create_event_role_name(event), reason=f"event {event} created", mentionable=True)
        # store event and role in database
        DiscordEvent(DBCONN).insert(event, event_role)
        # TODO: calender integration


    @staticmethod
    @BOT.event
    async def on_guild_scheduled_event_delete(event: ScheduledEvent) -> None:
        clog.info("event %s deleted", event)
        """
        - find the associated scheduled event role and delete it
        - set discord event state in database to cancelled
        """
        if event_role := get_role_for_event(event):
            await event_role.delete(reason=f"event {event} deleted")
        DiscordEvent(DBCONN).update_many(event.id, {"state": "cancelled", "notifier_role_id": None})


    @staticmethod
    @BOT.event
    async def on_guild_scheduled_event_update(event_before: ScheduledEvent, event_after: ScheduledEvent) -> None:
        # on: scheduled event name update
        if event_before.name != event_after.name:
            """
            - find the associated scheduled event role and update its name
            """
            clog.info(f"event {event_before} updated to {event_after}")
            if event_after_role := get_role_for_event(event_after):
                await event_after_role.edit(name=create_event_role_name(event_after), reason=f"event {event_after} updated")
        # TODO: update database entry
        discord_event_before = DiscordEvent(DBCONN).select_all(event_before.id)


    @staticmethod
    @BOT.event
    async def on_guild_scheduled_event_user_add(event: ScheduledEvent, user: ScheduledEventUser) -> None:
        """
        - give interested user the associated role
        """
        if event_role := get_role_for_event(event):
            if member := event.guild.get_member(user.id):
                await member.add_roles(event_role, reason=f"interested in event {event}")


    @staticmethod
    @BOT.event
    async def on_guild_scheduled_event_user_remove(event: ScheduledEvent, user: ScheduledEventUser) -> None:
        """
        - remove associated role from uninterested user
        """
        if event_role := get_role_for_event(event):
            if member := event.guild.get_member(user.id):
                await member.remove_roles(event_role, reason=f"uninterested in event {event}")



class Group__scheduled_event_state_tracking:
    @staticmethod
    @BOT.event
    async def on_voice_state_update(member: Member, state_before: VoiceState, state_after: VoiceState) -> None:
        # on: member joined voice channel
        if not state_before.channel and state_after.channel:
            await Group__scheduled_event_state_tracking.on_voice_member_joined(member, state_after.channel)
        # on: member left voice channel
        elif state_before.channel and not state_after.channel:
            await Group__scheduled_event_state_tracking.on_voice_member_left(member, state_before.channel)
        # on: member switched voice channel
        elif state_before.channel and state_after.channel and (state_before.channel.id != state_after.channel.id):
            await Group__scheduled_event_state_tracking.on_voice_member_left(member, state_before.channel)
            await Group__scheduled_event_state_tracking.on_voice_member_joined(member, state_after.channel)
        
        # on: member voice state changed, e.g. member is muted
        else:
            clog.debug("member %s voice state changed", member)


    @staticmethod
    async def on_voice_member_joined(member: Member, channel: VoiceChannel) -> None:
        global DBCONN
        clog.debug("member %s joined voice channel %s", member, channel)
        """
        - get latest (nearly) expired event for this channel from database
        - set state to active if scheduled
        - if updated state is active, add joined member to participated users
        """
        # get event from database as dict
        sql_select = "SELECT * FROM `{table}` WHERE (`channel_id` = ? AND `start_timestamp` <= ?) ORDER BY `start_timestamp` DESC".format(table=DiscordEvent.sql_table_name())
        if table_row := DBCONN.cursor().execute(sql_select, (channel.id, DiscordEvent.time_now(15))).fetchone():
            discord_event = DiscordEvent.table_row_to_dict(table_row)
            clog.debug("found expired event %s", discord_event)

            # set active if scheduled
            if discord_event["state"] == "scheduled":
                DiscordEvent(DBCONN).update(discord_event["id"], "state", "active")
                clog.debug("update event %s state from scheduled to active", discord_event["id"])

            # add member to participated users
            if discord_event["state"] in {"scheduled", "active"}:
                participated_user_ids = add_to_unique_list(json.loads(discord_event["participated_user_ids"]), member.id)
                DiscordEvent(DBCONN).update(discord_event["id"], "participated_user_ids", json.dumps(participated_user_ids))
                clog.debug("add member %s to participated users", member)
    
            
    @staticmethod
    async def on_voice_member_left(member: Member, channel: VoiceChannel) -> None:
        clog.debug("member %s left voice channel %s", member, channel)



class Group__slash_commands:
    @staticmethod
    @BOT.slash_command(name="ping", description="Get latency")
    async def sc_ping(interaction: Interaction) -> None:
        global BOT
        clog.debug("slash command used: /ping")
        await interaction.send(f"pong with {int(BOT.latency*1000)} ms latency")
    
    
    @staticmethod
    @BOT.slash_command(name="test", description="Temporary command to test specific something", default_member_permissions=Permissions(8))
    async def sc_test(interaction: Interaction) -> None:
        global BOT
        clog.info("slash command used: /test")
        
        var = DiscordEvent(DBCONN).select_all(1299043942318477394)
        print(var)
        
        await interaction.channel.send(pformat(var))


    @staticmethod
    @BOT.slash_command(name="create-test-event", description="Create an scheduled event for testing purposes", default_member_permissions=Permissions(8))
    async def sc_create_test_event(interaction: Interaction, event_name: str, event_channel: VoiceChannel, in_x_minutes: int) -> None:
        event = await interaction.guild.create_scheduled_event(
            entity_type=nextcord.ScheduledEventEntityType.voice,
            name=f"Test Event [{event_name}]",
            start_time=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=int(in_x_minutes)),
            channel=event_channel,
            reason="Event for testing purposes"
        )
        await interaction.channel.send(f"event {event} created")


    @staticmethod
    @BOT.slash_command(name="clear-test-events", description="Delete all test events", default_member_permissions=Permissions(8))
    async def sc_clear_test_events(interaction: Interaction) -> None:
        message = ""
        for event in interaction.guild.scheduled_events:
            if event.name.startswith("Test Event ["):
                await interaction.guild.get_scheduled_event(event.id).delete()
                message += f"event {event} deleted\n"
        if message:
            await interaction.channel.send(message)
        else:
            await interaction.channel.send("No test events found")



# get tokens and start bot
with open("tokens.json", "r", encoding="utf-8") as file:
    TOKENS = json.load(file)
BOT.run(TOKENS["discord"])
