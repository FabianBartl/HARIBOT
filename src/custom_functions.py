
import sqlite3
from sqlite3 import Connection
import json
from ast import literal_eval
from datetime import datetime, timezone

import nextcord
from nextcord import ScheduledEvent, ScheduledEventUser, ScheduledEventStatus
from nextcord import Interaction, VoiceState, VoiceChannel, Asset
from nextcord import Member, User, Role


class DiscordEvent:
    def __init__(self, *, scheduled_event: ScheduledEvent=None, notifier_role: Role=None) -> None:
        """
        TODO:
         - overload __init__ or else to support creation from scheduled event and loading from database
        """
        # base attributes of the scheduled event
        self.event_id: int    = scheduled_event.id
        self.title: str       = scheduled_event.name
        self.description: str = scheduled_event.description
        self.image_url: str   = scheduled_event.image.url if scheduled_event.image else ""
        self.creator_id: int  = scheduled_event.creator.id
        self.channel_id: int  = scheduled_event.channel_id
        
        # start and end datetime, with current scheduled event status
        self.start_timestamp: int         = int(scheduled_event.start_time.timestamp())
        self.end_timestamp: int|None      = int(scheduled_event.end_time.timestamp()) if scheduled_event.end_time else None
        self.timezone: timezone           = timezone.utc
        self.status: ScheduledEventStatus = ScheduledEventStatus.scheduled
        
        # list of users that are interested, were interested and participated in the scheduled event
        self.interested_user_ids: set[int]     = { user.id for user in scheduled_event.users }
        self.dis_interested_user_ids: set[int] = {}
        self.participated_user_ids: set[int]   = {}
        
        # notifier role and its usage counter
        if not notifier_role:
            notifier_role = get_role_for_event(scheduled_event)
        self.notifier_role_id: int   = notifier_role.id
        self.notifier_role_used: int = 0

        # the database table scheme for discord events
        self.__table_name = "discord_events"
        __sql_create_table = f"""
        CREATE TABLE `{self.__table_name}` (
            "id"          INTEGER NOT NULL UNIQUE,
            "title"       TEXT NOT NULL,
            "description" TEXT DEFAULT '',
            "image_url"   INTEGER DEFAULT '',
            "creator_id"  INTEGER NOT NULL,
            "channel_id"  INTEGER NOT NULL,
            
            "start_timestamp" INTEGER NOT NULL,
            "end_timestamp"   INTEGER DEFAULT NULL,
            "timezone"        TEXT NOT NULL DEFAULT 'utc',
            "status"          TEXT NOT NULL DEFAULT 'scheduled',
            
            "interested_user_ids"     json_array DEFAULT [],
            "dis_interested_user_ids" json_array DEFAULT [],
            "participated_user_ids"   json_array DEFAULT [],
            
            "notifier_role_id"   INTEGER DEFAULT NULL,
            "notifier_role_used" INTEGER DEFAULT 0,
            
            PRIMARY KEY("id"));
        """
    
    
    @classmethod
    def fetch_from_database(cls, *, connection: Connection) -> None:
        print(connection)
    
    
    def __convert_to_database_query_types(self) -> tuple[str|int|None]:
        sql_data = (
            int(self.event_id),
            str(self.title)[:64],
            str(self.description)[:512],
            str(self.image_url),
            int(self.creator_id),
            int(self.channel_id),
            
            int(self.start_timestamp),
            int(self.end_timestamp) if self.end_timestamp else None,
            str(self.timezone),
            str(self.status).rsplit(".", 1)[-1],
            
            json.dumps(list(self.interested_user_ids)),
            json.dumps(list(self.dis_interested_user_ids)),
            json.dumps(list(self.participated_user_ids)),
            
            int(self.notifier_role_id),
            int(self.notifier_role_used),
        )
        return sql_data

    
    def insert_into_database(self, connection: Connection) -> None:
        self.__sql_insert_into = f"INSERT INTO `{self.__table_name}` (`id`, `title`, `description`, `image_url`, `creator_id`, `channel_id`, `start_datetime`, `end_datetime`, `timezone`, `status`, `interested_user_ids`, `dis_interested_user_ids`, `participated_user_ids`, `notifier_role_id`, `notifier_role_used`) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);"
        # convert data into sql readable types and commit insert
        sql_data = self.__convert_to_database_query_types()
        connection.cursor().execute(self.__sql_insert_into, sql_data)
        connection.commit()



def create_event_role_name(event: ScheduledEvent) -> str:
    """
    - create role for a scheduled event: with humen readable name at front and bot readable id at the end 
    """
    return f"Ev:{event.name[:25]}:{event.id}"


def get_role_for_event(event: ScheduledEvent) -> Role|None:
    """
    - find the role for a scheduled event by searching for the event id in the role name
    """
    for role in event.guild.roles:
        if str(event.id) == role.name.rsplit(":", 1)[-1]:
            return role
    return None


def get_events_for_voice_channel(channel: VoiceChannel) -> list[ScheduledEvent]:
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
