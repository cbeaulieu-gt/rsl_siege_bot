import discord
from discord.ext import commands
import asyncio

from discord_api.discordClientUtils import get_guild_id

class DiscordAPI:
    def __init__(self, guild_id, bot_token):
        self._guild_id = guild_id
        intents = discord.Intents.default()
        intents.messages = True
        intents.guilds = True
        intents.members = True
        self.bot = commands.Bot(command_prefix="!", intents=intents)

        if not bot_token:
            raise ValueError("Bot token is required.")

        self.bot_token = bot_token
        self.bot_ready = False

        @self.bot.event
        async def on_ready():
            self.bot_ready = True
            print("Bot is ready!")

    async def start_bot(self):
        """
        Starts the bot in the background.
        """
        loop = asyncio.get_event_loop()
        loop.create_task(self.bot.start(self.bot_token))

    async def wait_until_ready(self):
        while not self.bot_ready:
            print("Waiting for the bot to initialize...")
            await asyncio.sleep(1)

    async def get_channel_id_by_name(self, channel_name):
        await self.wait_until_ready()
        """
        Retrieves the channel ID for a given channel name.
        """
        guild = discord.utils.get(self.bot.guilds, id=int(self.guild_id))
        if not guild:
            raise ValueError(f"Guild with ID {self.guild_id} not found.")

        channel = discord.utils.get(guild.channels, name=channel_name)
        if not channel:
            raise ValueError(f"Channel '{channel_name}' not found in guild '{self.guild_id}'.")

        return channel.id

    async def post_message(self, channel_name, message):
        await self.wait_until_ready()
        """
        Posts a message to a specified Discord channel.
        """
        channel_id = await self.get_channel_id_by_name(channel_name)
        channel = self.bot.get_channel(channel_id)
        if not channel:
            raise ValueError(f"Channel with ID {channel_id} not found.")

        return await channel.send(message)

    async def post_image(self, channel_name, image_path):
        await self.wait_until_ready()
        """
        Publishes an image to a Discord channel.
        """
        channel_id = await self.get_channel_id_by_name(channel_name)
        channel = self.bot.get_channel(channel_id)
        if not channel:
            raise ValueError(f"Channel with ID {channel_id} not found.")

        return await channel.send(file=discord.File(image_path))

    async def get_guild_members(self):
        await self.wait_until_ready()
        """
        Retrieves a list of all members in the guild along with their Discord name, guild nickname, and roles.
        """
        guild = discord.utils.get(self.bot.guilds, id=int(self.guild_id))
        if not guild:
            raise ValueError(f"Guild with ID {self.guild_id} not found.")

        members_info = []
        for member in guild.members:
            member_info = {
            "discord_name": member.name,
            "nickname": member.nick,
            "roles": [role.name for role in member.roles if role.name != "@everyone"]
            }
            members_info.append(member_info)

        return members_info

    async def get_guild_members_disc(self):
        """
        Retrieves a list of all discord.Member objects in the guild.

        Returns:
            list[discord.Member]: List of discord.Member objects in the guild.
        """
        await self.wait_until_ready()
        guild = discord.utils.get(self.bot.guilds, id=int(self.guild_id))
        if not guild:
            raise ValueError(f"Guild with ID {self.guild_id} not found.")
        return list(guild.members)

    async def send_message(self, member: discord.Member, message: str) -> None:
        """
        Sends a direct message (DM) to a specified Discord member.

        Args:
            member (discord.Member): The Discord member to send the message to.
            message (str): The message content to send.

        Raises:
            Exception: If the message could not be sent.
        """
        try:
            await member.send(message)
        except discord.Forbidden:
            print(f"Cannot DM {member.name}: Forbidden.")
        except Exception as e:
            print(f"Failed to send DM to {member.name}: {e}")

    async def get_role_id(self, role_name: str) -> int:
        """
        Retrieves the ID of a role in the guild by its name.

        Args:
            role_name (str): The name of the role to search for.

        Returns:
            int: The ID of the role if found.

        Raises:
            ValueError: If the role is not found in the guild.
        """
        await self.wait_until_ready()
        guild = discord.utils.get(self.bot.guilds, id=int(self.guild_id))
        if not guild:
            raise ValueError(f"Guild with ID {self.guild_id} not found.")
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            raise ValueError(f"Role '{role_name}' not found in guild '{self.guild_id}'.")
        return role.id

    @property
    def guild_id(self):
        """
        Returns the guild ID as a string.
        """
        return str(self._guild_id)


async def initialize_discord_client(guild_name, bot_token):
    guild_id = get_guild_id(guild_name)
    print(f"Using GUILDID: {guild_id}")
    discord_client = DiscordAPI(guild_id, bot_token=bot_token)

    await discord_client.start_bot()  # Start the bot in the background
    await discord_client.wait_until_ready()

    return discord_client