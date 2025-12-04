from discord_api.discordClient import DiscordAPI
import datetime
import configparser
from typing import List
import asyncio
import inspect
from clan.reminder_sent_store import ReminderSentStore
import signal
from logger import get_logger

# Module logger
logger = get_logger(__name__)

class Reminder:
    def __init__(self, event_name: str, reminder_day: int, discord_client: DiscordAPI = None, send_func=None, utc_time: int = None, sent_store: ReminderSentStore = None):
        self.event_name = event_name
        self.reminder_day = reminder_day  # 0=Monday, 1=Tuesday, ..., 6=Sunday
        self.send_func = send_func
        self.discord_client = discord_client
        self.utc_time = utc_time
        self.sent_store = sent_store or ReminderSentStore()
        self.channel = "announcements"  # Default channel

    @staticmethod
    def from_config(reminder_name: str, config: configparser.ConfigParser, discord_client: DiscordAPI = None, sent_store: ReminderSentStore = None) -> 'Reminder':
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
        # Get the target channel from config
        channel = None
        if "Channels" in config:
            channel = config["Channels"].get("reminders")
        reminder = Reminder(event_name=reminder_name, reminder_day=reminder_day, discord_client=discord_client, utc_time=utc_time, sent_store=sent_store)
        reminder.channel = channel or "announcements"
        return reminder

    def clear(self) -> None:
        """
        Clears the sent flag for this reminder for the current guild.
        """
        self.sent_store.clear(self.discord_client.guild_id, self.event_name)

    def should_send(self, day: datetime.date) -> bool:
        """
        Determines if the reminder should be sent for the given day and current time, based on config and reminder times.
        Args:
            day (datetime.date): The current date.
        Returns:
            bool: True if the reminder should be sent, False otherwise.
        """
        weekday = day.weekday()
        guild_id = self.discord_client.guild_id
        # Check if already sent today
        last_sent = self.sent_store.get(guild_id, self.event_name)
        if last_sent == str(day):
            print(f"[Reminder: {self.event_name}] Not sending: already sent today for guild {guild_id}.")
            return False
        # Check if today is the correct reminder day
        if weekday != self.reminder_day:
            print(f"[Reminder: {self.event_name}] Not sending: today (weekday={weekday}) is not the configured reminder day ({self.reminder_day}) for guild {guild_id}.")
            return False
        # Check if current UTC hour is after the configured reminder time
        hour = self.utc_time
        if hour is not None:
            now_utc = datetime.datetime.now(datetime.timezone.utc)
            if now_utc.hour < hour:
                print(f"[Reminder: {self.event_name}] Not sending: current UTC hour ({now_utc.hour}) is before configured reminder hour ({hour}) for guild {guild_id}.")
                return False
        return True

    async def send(self, day: datetime.date) -> None:
        """
        Sends the reminder and tracks the sent status in the config. Assumes all checks are done by caller.
        Args:
            day (datetime.date): The current date.
        """
        # Get send channel for reminders from config
        if self.send_func:
            if inspect.iscoroutinefunction(self.send_func):
                await self.send_func(self.discord_client, self.channel)
            else:
                self.send_func(self.discord_client, self.channel)
        else:
            raise ValueError(f"No send function defined for reminder '{self.event_name}'")
        self.sent_store.set(self.discord_client.guild_id, self.event_name, str(day))

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
    print(f"Sending reminder to channel '{channel}': {message}")
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

async def daily_callback_template(day: datetime.date, reminders: List[Reminder]) -> None:
    """
    Daily callback function to send reminders based on a list of Reminder objects.
    Each Reminder object handles its own send/tracking logic.
    Args:
        day (datetime.date): The current date when the callback is invoked.
        reminders (List[Reminder]): List of Reminder objects to check and send.
    """
    # If today is Sunday, clear all reminders for all guilds
    if day.weekday() == 6:
        for reminder in reminders:
            reminder.clear()
    for reminder in reminders:
        if reminder.should_send(day):
            await reminder.send(day)


async def heartbeat(discord_client: DiscordAPI, stop_event: asyncio.Event, channel: str = "heartbeat", interval: float = 1) -> None:
    """
    Background heartbeat task that posts a short heartbeat message at the given interval (in minutes) to the specified channel.
    The task runs until `stop_event` is set. Exceptions during sending are logged and the loop continues.
    Args:
        discord_client (DiscordAPI): Discord API client used to post messages.
        stop_event (asyncio.Event): Event used to request task stop/cleanup.
        channel (str): Channel name to post heartbeat messages to. Defaults to 'heartbeat'.
        interval (float): Interval in minutes between heartbeat messages. Defaults to 1.
    """
    try:
        while not stop_event.is_set():
            try:
                timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
                message = f":heartbeat: heartbeat at {timestamp}"
                logger.debug("Sending heartbeat to %s: %s", channel, message)
                await discord_client.post_message(channel, message)
            except Exception:
                logger.exception("Failed to send heartbeat message to channel '%s'", channel)
            # Wait up to 'interval' minutes, but return early if stop is requested
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval * 60)
            except asyncio.TimeoutError:
                continue
    finally:
        logger.info("heartbeat task exiting")


async def on_clock(callback, heartbeat_client: DiscordAPI = None, heartbeat_interval: float = 1,*args, **kwargs) -> None:
    """
    Periodically checks the current date and invokes the callback at the start of each new day.
    Optionally starts a heartbeat background task with the specified interval (in minutes).
    Args:
        callback (callable): The function to invoke at the start of the day. Must accept 'day' and any additional arguments.
        heartbeat_client (DiscordAPI): Optional Discord client to use for running the heartbeat background task.
        heartbeat_interval (float): Interval in minutes between heartbeat messages. Defaults to 1.
        *args: Additional positional arguments to pass to the callback.
        **kwargs: Additional keyword arguments to pass to the callback.
    """
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _request_stop() -> None:
        logger.info("Shutdown signal received; requesting on_clock stop.")
        loop.call_soon_threadsafe(lambda: stop_event.set())

    sigs = [getattr(signal, sig) for sig in ("SIGTERM", "SIGINT", "SIGHUP") if hasattr(signal, sig)]
    for sig in sigs:
        try:
            loop.add_signal_handler(sig, lambda _sig=sig: _request_stop())
        except NotImplementedError:
            logger.debug("Signal handlers not supported for %s", sig)

    heartbeat_task = None
    if heartbeat_client is not None:
        logger.info("Starting heartbeat task")
        heartbeat_task = asyncio.create_task(heartbeat(heartbeat_client, stop_event, interval=heartbeat_interval))

    try:
        while not stop_event.is_set():
            logger.info("Checking if it's time to send reminders at %s", datetime.datetime.now())
            today = datetime.datetime.now().date()
            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(today, *args, **kwargs)
                else:
                    def _sync_callback() -> None:
                        callback(today, *args, **kwargs)
                    await loop.run_in_executor(None, _sync_callback)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Exception raised while executing on_clock callback")
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=3600)
            except asyncio.TimeoutError:
                continue
    finally:
        logger.info("on_clock loop exiting gracefully")
        if heartbeat_task is not None:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
