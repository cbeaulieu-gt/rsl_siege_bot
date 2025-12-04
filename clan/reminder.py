"""
Reminder module for scheduling and sending Discord event notifications.
"""
import datetime
import inspect
import configparser
from typing import Optional, Callable, List
from clan.reminder_sent_store import ReminderSentStore
from clan.calendar import Calendar
from clan.events import Event

class Reminder:
    def __init__(
        self,
        event_type: Event,
        reminder_days: List[int],
        calendar: Calendar,
        discord_client: Optional = None,
        send_func: Optional[Callable] = None,
        utc_time: Optional[int] = None,
        sent_store: Optional[ReminderSentStore] = None
    ):
        """
        Initialize a Reminder instance.

        Args:
            event_type (Event): The event type as an Event enum.
            reminder_days (List[int]): List of days of the week (0=Monday, ..., 6=Sunday).
            calendar (Calendar): Calendar object for event scheduling.
            discord_client (Optional): Discord API client.
            send_func (Optional[Callable]): Function to send the reminder.
            utc_time (Optional[int]): UTC hour to send the reminder.
            sent_store (Optional[ReminderSentStore]): Store for sent reminders.
        """
        self.event_type = event_type
        self.reminder_days = reminder_days
        self.send_func = send_func
        self.discord_client = discord_client
        self.utc_time = utc_time
        self.sent_store = sent_store or ReminderSentStore()
        self.channel = "announcements"  # Default channel
        self.calendar = calendar

    @staticmethod
    def from_config(reminder_name: str, config: configparser.ConfigParser, calendar: Calendar, event_type: Event, discord_client: Optional = None, sent_store: Optional[ReminderSentStore] = None) -> 'Reminder':
        """
        Create a Reminder instance from the config for a given reminder name and event type.
        Args:
            reminder_name (str): The name of the reminder (e.g., 'Hydra', 'Chimera').
            config (configparser.ConfigParser): The loaded config object.
            calendar (Calendar): Calendar object for event scheduling.
            event_type (Event): The event type as an Event enum.
            discord_client (Optional): The Discord API client instance.
            sent_store (Optional[ReminderSentStore]): Store for sent reminders.
        Returns:
            Reminder: The instantiated Reminder object, or raises KeyError if not found.
        """
        if "Reminders" not in config:
            raise KeyError(f"No 'Reminders' section in config.")
        rem_cfg = config["Reminders"]
        if reminder_name not in rem_cfg:
            raise KeyError(f"No reminder named '{reminder_name}' in config.")
        # Parse comma-separated list of days
        days_str = rem_cfg.get(reminder_name)
        reminder_days = [int(day.strip()) for day in days_str.split(",")]
        utc_time = None
        if "ReminderTimes" in config:
            utc_time_str = config["ReminderTimes"].get(reminder_name.lower())
            if utc_time_str is not None:
                try:
                    utc_time = int(utc_time_str)
                except Exception:
                    utc_time = None
        # Get the target channel from config
        channel = None
        if "Channels" in config:
            channel = config["Channels"].get("reminders")
        reminder = Reminder(event_type=event_type, reminder_days=reminder_days, calendar=calendar, discord_client=discord_client, utc_time=utc_time, sent_store=sent_store)
        reminder.channel = channel or "announcements"
        return reminder

    def clear(self) -> None:
        """
        Clears the sent flag for this reminder for the current guild.
        """
        self.sent_store.clear(self.discord_client.guild_id, self.event_type.name)

    def reminder_number(self, day) -> int:
        """
        Returns the reminder number for the given day. If there is no reminder for the given day, returns -1.
        :param day: The day to check.
        :return: The reminder number (1-based index) or -1 if not a reminder day.
        """
        weekday = day.weekday()
        if weekday in self.reminder_days:
            return self.reminder_days.index(weekday) + 1
        return -1

    def should_send(self, day: Optional[datetime.date] = None) -> bool:
        """
        Determines if the reminder should be sent for the given day and current time, based on config, calendar, and reminder times.
        Args:
            day (Optional[datetime.date]): The current date. Uses today if not provided.
        Returns:
            bool: True if the reminder should be sent, False otherwise.
        """
        check_day = day or datetime.date.today()
        if self.calendar is not None and not self.calendar.is_event_week(self.event_type, check_day):
            print(f"[Reminder: {self.event_type.name}] Not sending: event is not active this week.")
            return False
        weekday = check_day.weekday()
        guild_id = self.discord_client.guild_id
        # Check if already sent today
        last_sent = self.sent_store.get(guild_id, self.event_type.name)
        if last_sent == str(check_day):
            print(f"[Reminder: {self.event_type.name}] Not sending: already sent today for guild {guild_id}.")
            return False
        # Check if today is one of the configured reminder days
        if weekday not in self.reminder_days:
            print(f"[Reminder: {self.event_type.name}] Not sending: today (weekday={weekday}) is not a configured reminder day {self.reminder_days} for guild {guild_id}.")
            return False
        # Check if current UTC hour is after the configured reminder time
        hour = self.utc_time
        if hour is not None:
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            if now_utc.hour < hour:
                print(f"[Reminder: {self.event_type.name}] Not sending: current UTC hour ({now_utc.hour}) is before configured reminder hour ({hour}) for guild {guild_id}.")
                return False
        return True

    async def send(self, day: datetime.date, *args) -> None:
        """
        Sends the reminder and tracks the sent status in the config. Assumes all checks are done by caller.
        Args:
            day (datetime.date): The current date.
        """
        # Get send channel for reminders from config
        if self.send_func:
            if inspect.iscoroutinefunction(self.send_func):
                await self.send_func(self.discord_client, self.channel, *args)
            elif callable(self.send_func):
                self.send_func(self.discord_client, self.channel, *args)
            else:
                raise ValueError(f"send_func for reminder '{self.event_type.name}' is not callable.")
        else:
            raise ValueError(f"No send function defined for reminder '{self.event_type.name}'")
        self.sent_store.set(self.discord_client.guild_id, self.event_type.name, str(day))
