from discord_api.discordClient import DiscordAPI
import datetime
import threading
import configparser
from typing import List
import asyncio
import inspect

class Reminder:
    def __init__(self, event_name: str, reminder_day: int, discord_client: DiscordAPI = None, send_func=None, utc_time: int = None):
        self.event_name = event_name
        self.reminder_day = reminder_day  # 0=Monday, 1=Tuesday, ..., 6=Sunday
        self.send_func = send_func
        self.discord_client = discord_client
        self.utc_time = utc_time

    @staticmethod
    def from_config(reminder_name: str, config: configparser.ConfigParser, discord_client: DiscordAPI = None) -> 'Reminder':
        """
        Create a Reminder instance from the config for a given reminder name.
        Args:
            reminder_name (str): The name of the reminder (e.g., 'Hydra', 'Chimera').
            config (configparser.ConfigParser): The loaded config object.
            discord_client (DiscordAPI): The Discord API client instance.
        Returns:
            Reminder: The instantiated Reminder object, or raises KeyError if not found.
        """
        if "Reminders" not in config:
            raise KeyError(f"No 'Reminders' section in config.")
        rem_cfg = config["Reminders"]
        if reminder_name not in rem_cfg:
            raise KeyError(f"No reminder named '{reminder_name}' in config.")
        reminder_day = int(rem_cfg.get(reminder_name))
        utc_time = None
        if "ReminderTimes" in config:
            utc_time_str = config["ReminderTimes"].get(reminder_name.lower())
            if utc_time_str is not None:
                try:
                    utc_time = int(utc_time_str)
                except Exception:
                    utc_time = None
        return Reminder(event_name=reminder_name, reminder_day=reminder_day, discord_client=discord_client, utc_time=utc_time)

    def clear(self, config: configparser.ConfigParser, config_path: str = "guild_config.ini") -> None:
        """
        Clears the sent flag for this reminder for the current guild.
        Args:
            config (configparser.ConfigParser): The loaded config object.
            config_path (str): Path to the configuration file.
        """
        if "RemindersSent" not in config:
            config["RemindersSent"] = {}
        sent_section = config["RemindersSent"]
        guild_id = getattr(self.discord_client, "guild_id", None)
        if guild_id is None:
            raise ValueError("Discord client does not have a guild_id attribute.")
        sent_key = f"{guild_id}_{self.event_name}Sent"
        if sent_key in sent_section:
            del sent_section[sent_key]
            with open(config_path, "w") as configfile:
                config.write(configfile)

    def should_send(self, day: datetime.date, config: configparser.ConfigParser, config_path: str = "guild_config.ini") -> bool:
        """
        Determines if the reminder should be sent for the given day and current time, based on config and reminder times.
        Args:
            day (datetime.date): The current date.
            config (configparser.ConfigParser): The loaded config object.
            config_path (str): Path to the configuration file.
        Returns:
            bool: True if the reminder should be sent, False otherwise.
        """
        weekday = day.weekday()
        if "RemindersSent" not in config:
            config["RemindersSent"] = {}
        sent_section = config["RemindersSent"]
        guild_id = getattr(self.discord_client, "guild_id", None)
        if guild_id is None:
            raise ValueError("Discord client does not have a guild_id attribute.")
        sent_key = f"{guild_id}_{self.event_name}Sent"
        # Check if already sent today
        if sent_section.get(sent_key, "").startswith(str(day)):
            return False
        # Check if today is the correct reminder day
        if weekday != self.reminder_day:
            return False
        # Check if current UTC hour is after the configured reminder time
        hour = self.utc_time
        if hour is not None:
            now_utc = datetime.datetime.utcnow()
            if now_utc.hour < hour:
                return False
        return True

    async def send(self, day: datetime.date, config: configparser.ConfigParser, config_path: str = "guild_config.ini", force: bool=False) -> None:
        """
        Sends the reminder and tracks the sent status in the config. Assumes all checks are done by caller.
        Args:
            day (datetime.date): The current date.
            config (configparser.ConfigParser): The loaded config object.
            config_path (str): Path to the configuration file.
        """
        if "RemindersSent" not in config:
            config["RemindersSent"] = {}
        sent_section = config["RemindersSent"]
        guild_id = getattr(self.discord_client, "guild_id", None)
        if guild_id is None:
            raise ValueError("Discord client does not have a guild_id attribute.")
        sent_key = f"{guild_id}_{self.event_name}Sent"

        # Get send channel for reminders from config
        if "Channels" not in config:    
            raise KeyError("No 'Channels' section in config.")
        channels_cfg = config["Channels"]
        if "reminders" not in channels_cfg: 
            raise KeyError("No 'reminders' channel defined in config.")
        ch = channels_cfg["reminders"]

        if self.send_func:
            if inspect.iscoroutinefunction(self.send_func):
                await self.send_func(self.discord_client, ch)
            else:
                self.send_func(self.discord_client, ch)
        else:
            raise ValueError(f"No send function defined for reminder '{self.event_name}'")
        sent_section[sent_key] = str(day)
        with open(config_path, "w") as configfile:
            config.write(configfile)

async def send_reminder_with_role(discord_client: DiscordAPI, message_body: str, role_name: str = "Member", channel: str = "announcements") -> None:
    """
    Sends a reminder message to the specified channel, mentioning the given role.
    Args:
        discord_client (DiscordAPI): The Discord API client instance.
        message_body (str): The main content of the reminder message (excluding the role mention).
        role_name (str): The name of the role to mention.
        channel (str): The channel to send the message to.
    """
    role_id = await discord_client.get_role_id(role_name)
    role_mention = f"<@&{role_id}>"
    message = f"{role_mention} {message_body}"
    await discord_client.post_message(channel, message)

async def send_hydra_reminder(discord_client: DiscordAPI, channel: str) -> None:
    """
    Sends a reminder message to the announcement channel that there is less than 24 hours left to do Hydra.
    Args:
        discord_client (DiscordAPI): The Discord API client instance.
    """
    message_body = (
        ":dragon_face: **Hydra Reminder!** :dragon_face:\n"
        "There are less than 24 hours left to do your Hydra keys!\n"
        "Don't forget to hit the boss and help the clan!"
    )
    await send_reminder_with_role(discord_client, message_body, channel=channel)

async def send_chimera_reminder(discord_client: DiscordAPI, channel: str) -> None:
    """
    Sends a reminder message to the announcement channel that there is less than 24 hours left to do Chimera.
    Args:
        discord_client (DiscordAPI): The Discord API client instance.
    """
    message_body = (
        ":japanese_ogre: **Chimera Reminder!** :japanese_ogre:\n"
        "There are less than 24 hours left to do your Chimera attempts!\n"
        "Make sure to participate and help the clan!"
    )
    await send_reminder_with_role(discord_client, message_body, channel=channel)

def initialize_reminders(config_path: str = "guild_config.ini", discord_client: DiscordAPI = None) -> List[Reminder]:
    """
    Initializes and returns a list of Reminder objects based on the Reminders config section.
    Uses the from_config method and dynamically resolves the send function by naming convention.
    Args:
        config_path (str): Path to the configuration file.
        discord_client (DiscordAPI): The Discord API client instance.
    Returns:
        List[Reminder]: List of Reminder objects.
    """
    config = configparser.ConfigParser()
    config.read(config_path)
    reminders: List[Reminder] = []
    if "Reminders" in config:
        rem_cfg = config["Reminders"]
        for reminder_name in rem_cfg:
            # Dynamically resolve the send function by naming convention
            func_name = f"send_{reminder_name.lower()}_reminder"
            send_func = globals().get(func_name)
            if send_func is not None:
                reminder = Reminder.from_config(reminder_name, config, discord_client=discord_client)
                reminder.send_func = send_func  # Ensure correct function is set
                reminders.append(reminder)
            else:
                raise ValueError(f"No send function found for reminder '{reminder_name}'. Expected function: {func_name}")
    return reminders

async def daily_callback_template(day: datetime.date, reminders: List[Reminder], config_path: str = "guild_config.ini") -> None:
    """
    Daily callback function to send reminders based on a list of Reminder objects.
    Each Reminder object handles its own send/tracking logic.
    Args:
        day (datetime.date): The current date when the callback is invoked.
        reminders (List[Reminder]): List of Reminder objects to check and send.
        config_path (str): Path to the configuration file.
    """
    config = configparser.ConfigParser()
    config.read(config_path)
    # If today is Sunday, clear all reminders for all guilds
    if day.weekday() == 6:
        for reminder in reminders:
            reminder.clear(config, config_path)
    for reminder in reminders:
        if reminder.should_send(day, config, config_path):
            await reminder.send(day, config, config_path)

async def on_clock(callback, sent_flags: dict, *args, **kwargs) -> None:
    """
    Periodically checks the current date and invokes the callback at the start of each new day.
    Ensures the callback is only invoked once per day by tracking sent_flags.
    Args:
        callback (callable): The function to invoke at the start of the day. Must accept 'day' as its first argument.
        sent_flags (dict): A dictionary to track if the reminder was sent for the current date.
        *args: Additional positional arguments to pass to the callback.
        **kwargs: Additional keyword arguments to pass to the callback.
    """
    import inspect
    while True:
        print(f"Checking if it's time to send reminders at {datetime.datetime.now()}")
        now = datetime.datetime.now()
        today = now.date()
        key = f"{callback.__name__}_{today}"
        if not sent_flags.get(key, False):
            if inspect.iscoroutinefunction(callback):
                await callback(today, *args, **kwargs)
            else:
                callback(today, *args, **kwargs)
            sent_flags[key] = True
        # Reset sent_flags for previous days to avoid memory growth
        for k in list(sent_flags.keys()):
            if str(today) not in k:
                del sent_flags[k]
        # Sleep for 1 hour before checking again
        await asyncio.sleep(3600)

