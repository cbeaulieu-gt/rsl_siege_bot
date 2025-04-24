from collections import namedtuple

import requests

post_image_response = namedtuple("PostImageResopnse", ["id", "cdn_url"])

class DiscordRequestHandler:
    def __init__(self, bot_token):
        self.base_url = "https://discord.com/api/v10"
        self.headers = {"Authorization": f"Bot {bot_token}"}
        self.channel_cache = {}  # Cache to store channel name-to-ID mapping

    def _make_request(self, method, endpoint, params=None, data=None, files=None):
        """
        Encapsulates the logic for making API requests.
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, params=params, data=data, files=files)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error during API call: {e}")
            return None

    def fetch_and_cache_channels(self, guild_id):
        """
        Fetches all channels in the guild and caches their names and IDs.
        """
        endpoint = f"/guilds/{guild_id}/channels"
        channels = self._make_request("GET", endpoint)
        if channels:
            self.channel_cache = {channel["name"]: channel["id"] for channel in channels}
        else:
            print("Failed to fetch channels.")

    def get_channel_id_by_name(self, guild_id, channel_name):
        """
        Retrieves the channel ID for a given channel name, using the cache if available.
        """
        if channel_name in self.channel_cache:
            return self.channel_cache[channel_name]

        # If not in cache, fetch and update the cache
        self.fetch_and_cache_channels(guild_id)
        return self.channel_cache.get(channel_name)

    def publish_image(self, guild_id, channel_name, image_path):
        """
        Publishes an image to a Discord channel.
        """
        channel_id = self.get_channel_id_by_name(guild_id, channel_name)
        if not channel_id:
            print(f"Channel '{channel_name}' not found in guild '{guild_id}'.")
            return None

        endpoint = f"/channels/{channel_id}/messages"
        with open(image_path, "rb") as image_file:
            files = {"file": image_file}
            response = self._make_request("POST", endpoint, files=files)

        if "attachments" in response and len(response["attachments"]) > 0:
            post_img_rsp = namedtuple("PostImageResponse", ["id", "cdn_url"])
            post_img_rsp.id = response["id"]
            post_img_rsp.cdn_url = response["attachments"][0]["url"]
            return post_img_rsp
        else:
            raise Exception("No image attachment found in response.")

    def post_message(self, guild_id, channel_name, message_content):
        """
        Posts a message to a specified Discord channel.
        """
        channel_id = self.get_channel_id_by_name(guild_id, channel_name)
        if not channel_id:
            print(f"Channel '{channel_name}' not found in guild '{guild_id}'.")
            return None

        endpoint = f"/channels/{channel_id}/messages"
        data = {"content": message_content}
        return self._make_request("POST", endpoint, data=data)