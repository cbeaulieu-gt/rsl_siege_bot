"""
Command Line Interface for the Siege Assignment System.

This module provides CLI commands for managing siege assignments, Discord bot operations,
and member management.
"""
import asyncio
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

import click

from siege.siege import (
    main_function,
    fetch_channel_members_function,
    print_assignments as siege_print_assignments,
)


# Constants
DEFAULT_GUILD = 'Personal'


@click.group()
@click.version_option(version='1.0.0', prog_name='Siege CLI')
def cli() -> None:
    """Siege Assignment Management CLI."""
    pass


@cli.command("run_siege")
@click.option(
    '--guild',
    default=DEFAULT_GUILD,
    help='The guild name to use for running commands.'
)
@click.option(
    '--send-dm',
    is_flag=True,
    default=False,
    help='Send DMs to members about assignment changes.'
)
@click.option(
    '--post-message',
    is_flag=True,
    default=False,
    help='Post assignment images and messages to Discord channels.'
)
def run_siege(guild: str, send_dm: bool, post_message: bool) -> None:
    """
    Process siege assignments and optionally send notifications.
    
    This command processes the latest siege assignment files, compares changes,
    and can optionally post messages to Discord channels and send DMs to members.
    
    Args:
        guild: The Discord guild name to process.
        send_dm: Whether to send direct messages to members about changes.
        post_message: Whether to post assignment images and messages to channels.
    """
    try:
        asyncio.run(main_function(guild, send_dm, post_message))
    except KeyboardInterrupt:
        click.echo("Operation cancelled by user.", err=True)
    except Exception as e:
        click.echo(f"Error running siege command: {e}", err=True)
        raise click.Abort()


@cli.command("run_bot")
@click.option(
    '--guild',
    required=True,
    help='The guild name to use for running the bot.'
)
def run_bot(guild: str) -> None:
    """
    Run the Discord bot in interactive mode.
    
    This command starts the Discord bot for the specified guild,
    allowing for real-time interaction and command processing.
    
    Args:
        guild: The Discord guild name to connect to.
    """
    try:
        # Import here to avoid circular imports and missing dependencies
        from siege.siege import run_bot_function
        asyncio.run(run_bot_function(guild))
    except ImportError as e:
        click.echo(f"Bot functionality not available: {e}", err=True)
        raise click.Abort()
    except KeyboardInterrupt:
        click.echo("Bot stopped by user.", err=True)
    except Exception as e:
        click.echo(f"Error running bot: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option(
    '--guild',
    required=True,
    help='The guild name to use for fetching members.'
)
def fetch_members(guild: str) -> None:
    """
    Fetch and display all members in the specified guild.
    
    This command retrieves information about all members in the Discord guild,
    including their usernames and nicknames.
    
    Args:
        guild: The Discord guild name to fetch members from.
    """
    try:
        asyncio.run(fetch_channel_members_function(guild))
    except Exception as e:
        click.echo(f"Error fetching members: {e}", err=True)
        raise click.Abort()


@cli.command()
def assignments() -> None:
    """
    Print all assignments from the most recent siege assignment file.
    
    This command scans for the latest siege assignment Excel file and displays
    all member assignments to the console.
    """
    try:
        siege_print_assignments()
    except FileNotFoundError:
        click.echo("No siege assignment files found.", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error reading assignments: {e}", err=True)
        raise click.Abort()


@cli.command("run_reminders")
@click.option(
    '--guild',
    default=DEFAULT_GUILD,
    help='The guild name to use for running commands.'
)
def run_reminders(guild) -> None:
    """
    Initializes the reminder set and starts the daily reminder loop.
    """
    from clan.clan import run_reminders_loop
    run_reminders_loop(guild)


@cli.command("send_reminders")
@click.option(
    '--guild',
    default=DEFAULT_GUILD,
    help='The guild name to use for running commands.'
)
def send_reminders(guild) -> None:
    """
    Immediately sends all reminders for today and exits.
    """
    from clan.clan import send_reminders_once
    send_reminders_once(guild)


def main() -> None:
    """Entry point for the CLI application."""
    cli()


if __name__ == '__main__':
    main()
