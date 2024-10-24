
import json
import sqlite3
import datetime
from sqlite3 import Connection
from ast import literal_eval
from typing import Any

import nextcord
from nextcord import ScheduledEvent, ScheduledEventUser, ScheduledEventStatus
from nextcord import Interaction, VoiceState, VoiceChannel, Asset
from nextcord import Member, User, Role


class DiscordEvent:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection
        # the database table scheme for discord events
        f"""
        CREATE TABLE `{self.__sql_table_name()}` (
            "id"          INTEGER NOT NULL UNIQUE,
            "title"       TEXT NOT NULL,
            "description" TEXT DEFAULT '',
            "image_url"   INTEGER DEFAULT '',
            "creator_id"  INTEGER DEFAULT NULL,
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
    
    def __sql_table_name(self) -> str:
        return "discord_events"
    
    def __sql_table_coloumns(self) -> tuple[str]:
        return ("id", "title", "description", "image_url", "creator_id", "channel_id", "start_timestamp", "end_timestamp", "timezone", "status", "interested_user_ids", "dis_interested_user_ids", "participated_user_ids", "notifier_role_id", "notifier_role_used")
    
    def __sql_coloumns_str(self) -> str:
        return "("+", ".join([ f"`{coloumn}`" for coloumn in self.__sql_table_coloumns() ])+")"


    def insert(self, scheduled_event: ScheduledEvent, notifier_role: Role|None) -> None:
        """
        - fill table coloumns with properties from the scheduled event and defaults
        - insert into table 
        """
        sql_data = (
            # base attributes of the scheduled event
            int(scheduled_event.id),                                                # id
            str(scheduled_event.name)[:128],                                        # title
            str(scheduled_event.description)[:512],                                 # description
            str(scheduled_event.image.url) if scheduled_event.image else "",        # image_url
            int(scheduled_event.creator.id) if scheduled_event.creator else None,   # creator_id
            int(scheduled_event.channel_id),                                        # channel_id
            
            # start and end datetime, with current scheduled event status
            int(scheduled_event.start_time.timestamp()),                                        # start_timestamp
            int(scheduled_event.end_time.timestamp()) if scheduled_event.end_time else None,    # end_timestamp
            str(datetime.timezone.utc),                                                         # timezone
            str(ScheduledEventStatus.scheduled).rsplit(".", 1)[-1],                             # status
            
            # list of users that are interested, were interested and participated in the scheduled event
            json.dumps(list({ user.id for user in scheduled_event.users })),    # interested_user_ids
            "[]",                                                               # dis_interested_user_ids
            "[]",                                                               # participated_user_ids
                        
            # notifier role and its usage counter
            int(notifier_role.id) if notifier_role else None,   # notifier_role_id
            0                                                   # notifier_role_used
        )
        
        # insert discord event data into database table
        sql_insert_into = "INSERT INTO `{table}` {coloumns} VALUES {values};".format(
            table=self.__sql_table_name(),
            coloumns=self.__sql_coloumns_str(),
            values="("+",".join(["?"]*len(self.__sql_table_coloumns))+")"
        )
        self.connection.cursor().execute(sql_insert_into, sql_data)
        self.connection.commit()


    def select(self, event_id: int, coloumn: str) -> str|int|None:
        event_id = int(event_id)
        coloumn = str(coloumn)
        """
        - check if coloumn exists in table
        - select single coloumn of table entry by unique event id and return its value
        """
        if not coloumn in self.__sql_table_coloumns():
            raise KeyError(f"coloumn `{coloumn}` does not exist in database table `{self.__sql_table_name()}`")

        sql_select = "SELECT ? FROM `{table}` WHERE `id` = ?".format(table=self.__sql_table_name())
        row = self.connection.cursor().execute(sql_select, (coloumn, event_id)).fetchone()
        return row[0]


    def select_all(self, event_id: int) -> dict[str: str|int|None]:
        event_id = int(event_id)
        """
        - select table entry by unique event id
        - zip entry tuple with table coloumn names and return as dictionary
        """
        sql_select = "SELECT * FROM `{table}` WHERE `id` = ?".format(table=self.__sql_table_name())
        table_row = self.connection.cursor().execute(sql_select, (event_id,)).fetchone()
        discord_event = { coloumn: value for (coloumn, value) in zip(self.__sql_table_coloumns(), table_row) }
        return discord_event


    def update(self, event_id: int, coloumn: str, value: str|int|None) -> None:
        event_id = int(event_id)
        coloumn = str(coloumn)
        """
        - check if coloumn exists in table
        - update single coloumn value of an event
        """
        if not coloumn in self.__sql_table_coloumns():
            raise KeyError(f"coloumn `{coloumn}` does not exist in database table `{self.__sql_table_name()}`")
        
        sql_update = "UPDATE `{table}` SET ? = ? WHERE `id` = ?".format(table=self.__sql_table_name())
        self.connection.cursor().execute(sql_update, (coloumn, value, event_id))
    
    
    def update_many(self, event_id: int, coloumn_values: dict[str: str|int|None]) -> None:
        event_id = int(event_id)
        for coloumn, value in coloumn_values.items():
            self.update(event_id, coloumn, value)
    
    
    def delete(self, event_id: int) -> None:
        event_id = int(event_id)
        """
        - deletes the event entry
        """
        sql_delete = "DELETE FROM `{table}` WHERE `id` = ?".format(table=self.__sql_table_name())
        self.connection.cursor().execute(sql_delete, (event_id,))



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
