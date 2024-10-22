import nextcord
from nextcord import ScheduledEvent, ScheduledEventUser
from nextcord import Interaction, VoiceState, VoiceChannel
from nextcord import Member, User, Role


def create_event_role_name(event: ScheduledEvent) -> str:
    """
    - create role for a scheduled event: with humen readable name at front and bot readable id at the end 
    """
    return f"Ev:{event.name[:25]}:{event.id}"


async def get_role_for_event(event: ScheduledEvent) -> Role|None:
    """
    - find the role for a scheduled event by searching for the event id in the role name
    """
    for role in event.guild.roles:
        if str(event.id) == role.name.rsplit(":", 1)[-1]:
            return role
    return None


async def get_events_for_voice_channel(channel: VoiceChannel) -> list[ScheduledEvent]:
    """
    - returns all scheduled events that are planned for the given channel
    """
    channel_events = [ event for event in channel.guild.scheduled_events if event.channel_id is channel.id ]
    return channel_events


async def update_scheduled_event_state(event: ScheduledEvent) -> None:
    """ [triggered by on_event callbacks that may cause an scheduled event state update]
    - try to find out the scheduled event state
    - perform needed actions depending on this state (e.g.: deleting scheduled event roles, updating calender metadata)
    """
    # on: scheduled event not found (because its deleted/canceled/completed)
    if not event.guild.get_scheduled_event(event.id):
        """
        - delete associated role
        - TODO: update calender metadata depending on cause
        """
        if event_role := get_role_for_event(event):
            await event_role.delete(reason=f"event {event} not found")
