import datetime
import pickle
import os.path
import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


class CalendarManager:
    def __init__(self) -> None:
        # If modifying these scopes, delete the file token.pickle.
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.CREDENTIALS_FILE = os.path.join("..", 'google_api_credentials.json')
        self.SAVE_FOLDER = os.path.join('..', 'data', 'googleCalendar')
        self.TOKEN_FILE_SCHEME = '-token.pickle'
        self.EVENT_FILE_SCHEME = '-eventIds.json'

        self.flows = {}

    def get_event_ids(self, guild_id):
        """Load discord event to Google calendar ID assignments for one guild."""

        event_path = os.path.join(self.SAVE_FOLDER, str(guild_id) + self.EVENT_FILE_SCHEME)

        if not os.path.exists(event_path):
            return {}

        with open(event_path, "r") as file:
            parsed_json = json.load(file)
        return parsed_json

    def save_event_ids(self, guild_id, ids):
        """Save discord event to Google calendar ID assignments for one guild."""

        event_path = os.path.join(self.SAVE_FOLDER, str(guild_id) + self.EVENT_FILE_SCHEME)

        with open(event_path, 'w') as file:
            json.dump(ids, file)

    def get_calendar_service(self, guild_id):
        """Get the Google calendar service for one guild, if guild is connected to a calendar.
        This service is needed to modify/add entries to a Calendar.
        """

        token_path = os.path.join(self.SAVE_FOLDER, str(guild_id) + self.TOKEN_FILE_SCHEME)
        creds = None

        # check if the guild has valid credentials to modify a Calendar
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            # refresh credentials if possible
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as _:
                    return None

                # Save the credentials for the next run
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)

            # no valid credentials
            else:
                return None

        # create the service
        service = build('calendar', 'v3', credentials=creds)
        return service

    def create_sign_up_link(self, guild_id):
        """Check if the guild has valid credentials to modify a calendar and generate a signup-url if not.
        Returns signup-url, or None if already signed up!
        Call "save_sign_up_code()" with the code from the Ulr to confirm the connection.
        """

        token_path = os.path.join(self.SAVE_FOLDER, str(guild_id) + self.TOKEN_FILE_SCHEME)
        creds = None
        auth_url = None

        # check if the guild already has valid credentials
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            # refresh credentials if possible
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as _:
                    return None

                # Save the credentials for the next run
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)

            # create a signup link, if there are no (valid) credentials available
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CREDENTIALS_FILE, scopes=self.SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
                self.flows[guild_id] = flow

                auth_url, _ = flow.authorization_url(prompt='consent')

        return auth_url

    def save_sign_up_code(self, guild_id, code):
        """Confirm a connection to a Google calendar, initiated in "create_sign_up_link".
        Returns True if the connection attempt was successful.
        """

        token_path = os.path.join(self.SAVE_FOLDER, str(guild_id) + self.TOKEN_FILE_SCHEME)

        # only possible if a connection attempt was initiated in this guild
        if guild_id in self.flows.keys():
            flow = self.flows[guild_id]
        else:
            return False

        try:
            flow.fetch_token(code=code)
            creds = flow.credentials
            # save the credentials
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
            return True

        except Exception as _:
            # invalid code entered by the user
            return False

    def delete_credentials(self, guild_id):
        """Delete the Google calendar credentials for one guild.
        Returns True if the guild even had a connection.
        """

        token_path = os.path.join(self.SAVE_FOLDER, str(guild_id) + self.TOKEN_FILE_SCHEME)

        if os.path.exists(token_path):
            os.remove(token_path)
            return True
        return False

    def create_calendar_entry(self, guild_id, id_, name, description, start_time, end_time):
        """Create a Google Calendar event.
        guild_id:       discord guild id
        id_:            discord event id
        name:           entry name
        description:    entry description
        start_time:     starting time as unix timestamp
        end_time:       ending time as unix timestamp

        returns True if successful
        """

        service = self.get_calendar_service(guild_id)

        if service is not None:
            start = start_time.isoformat()
            end = (end_time if end_time is not None else (start_time + datetime.timedelta(hours=2))).isoformat()

            # create the event
            event_result = service.events().insert(calendarId='primary',
                                                   body={
                                                       "summary": name,
                                                       "description": description,
                                                       "start": {"dateTime": start,
                                                                 "timeZone": 'Asia/Kolkata'},
                                                       "end": {"dateTime": end,
                                                               "timeZone": 'Asia/Kolkata'},
                                                   }
                                                   ).execute()

            # save the Google calendar event ID in case the event needs to be modified/deleted later on
            event_ids = self.get_event_ids(guild_id)
            event_ids[str(id_)] = event_result['id']
            self.save_event_ids(guild_id, event_ids)

            return True

        return False

    def delete_calendar_entry(self, guild_id, id_):
        """Find a scheduled event by discord event ID and delete it."""

        service = self.get_calendar_service(guild_id)

        if service is not None:
            try:
                # find and remove event
                event_ids = self.get_event_ids(guild_id)
                service.events().delete(eventId=event_ids[str(id_)], calendarId="primary").execute()
            except Exception as _:
                # no entry with specified ID
                pass

    def update_calendar_entry(self, user_id, id_, name, description, start_time, end_time):
        """Find a scheduled event by discord event ID and update its parameters.
        Returns True if successful
        """

        # delete the old event and replace it with a new one
        self.delete_calendar_entry(user_id, id_)
        return self.create_calendar_entry(user_id, id_, name, description, start_time, end_time)
