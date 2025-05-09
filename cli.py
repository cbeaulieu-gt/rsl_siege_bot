import asyncio

import click
from siege import main_function, fetch_channel_members_function

@click.group()
def cli():
    pass


@cli.command(name='run_siege')
@click.option('--guild', default='Personal', help='The guild name to use for running commands.')
def run_siege(guild):
    """Main entry point for the script."""
    asyncio.run(main_function(guild))

@cli.command(name='fetch_guild_members')
@click.option('--guild', required=True, help='The guild name to use for fetching channel members.')
def fetch_channel_members(guild):
    """Fetch and display all members in a given channel."""
    asyncio.run(fetch_channel_members_function(guild))

@cli.command(name='print_assignments')
def print_assignments():
    """
    Print all assignments from the upcoming siege assignment Excel file.
    """
    from siege import print_assignments as siege_print_assignments
    siege_print_assignments()

if __name__ == '__main__':
    cli()
