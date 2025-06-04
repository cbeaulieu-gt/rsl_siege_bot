import discord
from discord.ext import commands
import asyncio
from typing import Callable, Dict, List

from discord_api.discordClientUtils import get_guild_id

class DiscordAPI:
    def __init__(self, guild_id, bot_token):
        self.guild_id = guild_id
        self.channel_listeners: Dict[int, List[Callable]] = {}  # Store channel listeners
        intents = discord.Intents.default()
        intents.messages = True
        intents.guilds = True
        intents.members = True
        intents.message_content = True  # Required for message content access
        self.bot = commands.Bot(command_prefix="!", intents=intents)

        if not bot_token:
            raise ValueError("Bot token is required.")

        self.bot_token = bot_token
        self.bot_ready = False

        @self.bot.event
        async def on_ready():
            self.bot_ready = True
            print("Bot is ready!")

        @self.bot.event
        async def on_message(message):
            # Don't respond to bot's own messages
            if message.author == self.bot.user:
                return
            
            # Check if there are listeners for this channel
            channel_id = message.channel.id
            if channel_id in self.channel_listeners:
                for callback in self.channel_listeners[channel_id]:
                    try:
                        # Call the callback function with the message
                        if asyncio.iscoroutinefunction(callback):
                            await callback(message)
                        else:
                            callback(message)
                    except Exception as e:
                        print(f"Error in channel listener callback: {e}")

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

    async def bind_channel_listener(self, channel_id: int, callback: Callable) -> None:
        """
        Binds a listener function to a specific channel that will be invoked when new messages are posted.

        Args:
            channel_id (int): The ID of the channel to listen to.
            callback (Callable): The function to call when a message is received. 
                                Can be sync or async. Will receive the discord.Message object as argument.

        Raises:
            ValueError: If the channel is not found.
        """
        await self.wait_until_ready()
        
        # Verify the channel exists and is accessible
        channel = self.bot.get_channel(channel_id)
        if not channel:
            raise ValueError(f"Channel with ID {channel_id} not found or not accessible.")
        
        # Add the callback to the listeners for this channel
        if channel_id not in self.channel_listeners:
            self.channel_listeners[channel_id] = []
        
        self.channel_listeners[channel_id].append(callback)
        print(f"Listener bound to channel '{channel.name}' (ID: {channel_id})")

    async def unbind_channel_listener(self, channel_id: int, callback: Callable = None) -> None:
        """
        Unbinds a listener function from a specific channel.

        Args:
            channel_id (int): The ID of the channel to stop listening to.
            callback (Callable, optional): The specific callback to remove. 
                                         If None, removes all listeners for the channel.
        """
        if channel_id not in self.channel_listeners:
            return
        
        if callback is None:
            # Remove all listeners for this channel
            del self.channel_listeners[channel_id]
            print(f"All listeners removed from channel ID: {channel_id}")
        else:
            # Remove specific callback
            if callback in self.channel_listeners[channel_id]:
                self.channel_listeners[channel_id].remove(callback)
                print(f"Specific listener removed from channel ID: {channel_id}")
                
                # Clean up empty listener list
                if not self.channel_listeners[channel_id]:
                    del self.channel_listeners[channel_id]

    async def bind_channel_listener_by_name(self, channel_name: str, callback: Callable) -> None:
        """
        Binds a listener function to a specific channel by name.

        Args:
            channel_name (str): The name of the channel to listen to.
            callback (Callable): The function to call when a message is received.

        Raises:
            ValueError: If the channel is not found.
        """
        channel_id = await self.get_channel_id_by_name(channel_name)
        await self.bind_channel_listener(channel_id, callback)

    def get_active_listeners(self) -> Dict[int, int]:
        """
        Returns a dictionary of active channel listeners.

        Returns:
            Dict[int, int]: Mapping of channel_id to number of listeners.
        """
        return {channel_id: len(callbacks) for channel_id, callbacks in self.channel_listeners.items()}

async def initialize_discord_client(guild_name, bot_token):
    guild_id = get_guild_id(guild_name)
    print(f"Using GUILDID: {guild_id}")
    discord_client = DiscordAPI(guild_id, bot_token=bot_token)

    await discord_client.start_bot()  # Start the bot in the background
    await discord_client.wait_until_ready()

    return discord_client