
import json
import os, sys

import nextcord
from nextcord import Interaction, ScheduledEvent
from nextcord.ext import commands

BOT = commands.Bot()
SERVER_IDS = [1023614599502774362]


@BOT.event
async def on_connect():
    print("bot connected")

@BOT.event
async def on_ready():
    print(f"bot logged in as {BOT.user}")
    await BOT.sync_all_application_commands()
    print("commands synced")
        
@BOT.event
async def on_close():
    print("bot shut down")

@BOT.event
async def on_disconnect():
    print("bot disconnected")


@BOT.event
async def on_guild_scheduled_event_create(_event: ScheduledEvent):
    """
    - create role for event containing name and id
    - add event to calender by @noeppi-noeppi
    """
    event = await _event.guild.fetch_scheduled_event(_event.id)
    print(f"event '{event.name}' ({event.id}) created")
    event_role_name = f"Ev:{event.name[:25]}:{event.id}"
    await event.guild.create_role(name=event_role_name, reason=f"event {event.id} created", mentionable=True)
    # TODO: calender integration

@BOT.event
async def on_guild_scheduled_event_delete(event: ScheduledEvent):
    """
    - get all roles
    - find corresponding event role and delete it
    """
    print(f"event '{event.name}' ({event.id}) deleted")
    all_roles = await event.guild.fetch_roles()
    for role in all_roles:
        if str(event.id) in role.name.rsplit(":", 1)[-1]:
            await role.delete(reason=f"event {event.id} deleted")

@BOT.event
async def on_guild_scheduled_event_update(event_before: ScheduledEvent, event_after: ScheduledEvent):
    """
    - get all roles
    - find corresponding event role and update its name
    """
    print(f"event '{event_before.name}' ({event_before.id}) updated [to '{event_after.name}']")
    all_roles = await event_before.guild.fetch_roles()
    event_new_role_name = f"Ev:{event_after.name[:25]}:{event_after.id}"
    for role in all_roles:
        if str(event_before.id) in role.name.rsplit(":", 1)[-1]:
            await role.edit(name=event_new_role_name, reason=f"event {event_after.id} updated")


@BOT.slash_command(name="ping", description="Test latency", guild_ids=SERVER_IDS)
async def ping(interaction: Interaction):
    print("slash command used: /ping")
    await interaction.send(f"pong with {BOT.latency*1_000:.0f} ms latency")


# read token and start bot
with open("tokens.json", "r", encoding="utf-8") as file:
    TOKENS = json.load(file)
BOT.run(TOKENS["discord"])
