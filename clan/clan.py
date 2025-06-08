from clan.clan_reminders import initialize_reminders, daily_callback_template, on_clock
from config import BOTTOKEN
from discord_api.discordClient import initialize_discord_client
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

def run_reminders_loop(guild_name: str):
    """
    Initializes the reminder set and starts the daily reminder loop for the specified guild.
    """
    async def _main():
        discord_client = await initialize_discord_client(guild_name, bot_token=BOTTOKEN)
        reminders = initialize_reminders(config_path="guild_config.ini", discord_client=discord_client)
        sent_flags = {}
        on_clock(
            daily_callback_template,
            sent_flags,
            reminders,
            "guild_config.ini"
        )
        print(f"Reminder loop started for guild '{guild_name}'. Reminders will be sent automatically each day.")
    asyncio.run(_main())


def send_reminders_once(guild_name: str):
    """
    Immediately sends all reminders for today for the specified guild and exits.
    """
    async def _main():
        discord_client = await initialize_discord_client(guild_name, bot_token=BOTTOKEN)
        reminders = initialize_reminders(config_path="guild_config.ini", discord_client=discord_client)
        config = get_config_parser()
        for reminder in reminders:
            await reminder.send(datetime.date.today(), config, "guild_config.ini", force=True)
    asyncio.run(_main())
