from clan.clan_reminders import initialize_reminders, daily_callback_template, on_clock
from discord_api.discordClient import initialize_discord_client
from discord_api.discordClientUtils import DiscordUtils
import datetime
import asyncio
import configparser

def get_config_parser(config_path: str = "guild_config.ini") -> configparser.ConfigParser:
    """
    Returns a ConfigParser instance for the specified configuration file.
    Args:
        config_path (str): Path to the configuration file.
    Returns:
        configparser.ConfigParser: ConfigParser instance with the loaded configuration.
    """
    config = configparser.ConfigParser()
    config.read(config_path)
    return config

def run_reminders_loop(guild_name: str, send_heartbeart):
    """
    Initializes the reminder set and starts the daily reminder loop for the specified guild.
    :param send_heartbeart: Tells the bot to periodically send a heartbeat to a channel called "heartbeat".
    """
    async def _main():
        bot_token = DiscordUtils.get_bot_token()
        discord_client = await initialize_discord_client(guild_name, bot_token=bot_token)
        reminders = initialize_reminders(config_path="guild_config.ini", discord_client=discord_client)
        heartbeat_client = discord_client if send_heartbeart else None

        print(f"Reminder loop started for guild '{guild_name}'. Reminders will be sent automatically each day.")
        await on_clock(
            daily_callback_template,
            heartbeat_client,
            reminders
        )
       
    asyncio.run(_main())


def send_reminders_once(guild_name: str):
    """
    Immediately sends all reminders for today for the specified guild and exits.
    """
    async def _main():
        bot_token = DiscordUtils.get_bot_token()
        discord_client = await initialize_discord_client(guild_name, bot_token=bot_token)
        reminders = initialize_reminders(config_path="guild_config.ini", discord_client=discord_client)
        for reminder in reminders:
            await reminder.send(datetime.date.today())
    asyncio.run(_main())
