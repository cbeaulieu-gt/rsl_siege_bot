import os
import sys
from collections import namedtuple
from datetime import time
from time import sleep

from discord_api.discordRequestHandler import DiscordRequestHandler, post_image_response
from discord_api.discordMemberFetcher import DiscordMemberFetcher, Member
from config import BOTTOKEN

class DiscordAPI:
    def __init__(self, guild_id):
        self.guild_id = guild_id
        self.api_client = DiscordRequestHandler(BOTTOKEN)

    def format_discord_link(self, channel, message_id):
        channel_id = self.api_client.get_channel_id_by_name(self.guild_id, channel)
        return f"https://discord.com/channels/{self.guild_id}/{channel_id}/{message_id}"

    def get_members(self):
        member_fetcher = DiscordMemberFetcher(self.api_client, self.guild_id)
        members = member_fetcher.fetch_all_members()

        member_list = []
        for m in members:
            member = Member.from_api(m)
            member_list.append(member)

        return member_list

    def post_image(self, path: str, channel: str="clan-siege-images", delay=1) -> post_image_response:
        if delay > 0:
            sleep(delay)
        return self.api_client.publish_image(self.guild_id, channel, path)

    def post_message(self, message: str, channel, delay=1) -> str:
        if delay > 0:
            sleep(delay)
        response = self.api_client.post_message(self.guild_id, channel, message)
        return response["id"]