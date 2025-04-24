import os
import sys
from collections import namedtuple
from datetime import time
from time import sleep

from discord_api.discordRequestHandler import DiscordRequestHandler, post_image_response
from discord_api.discordMemberFetcher import DiscordMemberFetcher, Member
from config import BOTTOKEN

GUILD_ID = "1298470807915331738"

def format_discord_link(channel, message_id):
    api_client = DiscordRequestHandler(BOTTOKEN)
    channel_id = api_client.get_channel_id_by_name(GUILD_ID, channel)
    return f"https://discord.com/channels/{GUILD_ID}/{channel_id}/{message_id}"

def get_members():
    # Initialize the API client and member fetcher
    api_client = DiscordRequestHandler(BOTTOKEN)
    member_fetcher = DiscordMemberFetcher(api_client, GUILD_ID)

    # Fetch all members
    members = member_fetcher.fetch_all_members()

    # Convert to a list of Member objects
    member_list = []
    for m in members:
        member = Member.from_api(m)
        member_list.append(member)

    return member_list

def post_image(path: str, channel: str="clan-siege-images", delay=1) -> post_image_response:
    if delay > 0:
        sleep(delay)

    # Initialize the API client and member fetcher
    api_client = DiscordRequestHandler(BOTTOKEN)
    return api_client.publish_image(GUILD_ID, channel,path)

def post_message(message: str, channel, delay=1) -> str:
    if delay > 0:
        sleep(delay)

    api_client = DiscordRequestHandler(BOTTOKEN)
    response = api_client.post_message(GUILD_ID, channel, message)
    return response["id"]