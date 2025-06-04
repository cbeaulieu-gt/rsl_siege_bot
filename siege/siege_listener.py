"""
Discord message listener for the Siege Assignment System.

This module provides event handlers and message processing functionality
for Discord bot interactions related to siege assignments.
"""
import asyncio
import logging
from typing import Optional, Dict, Any, Callable, Awaitable

import discord
from discord.ext import commands

from discord_api.discordClient import DiscordAPI


# Configure logging
logger = logging.getLogger(__name__)


from typing import Callable, Awaitable, TypeAlias

# Define type aliases for better readability
UserId = str
Username = str
Channel = str
Message = str
Response = str

# Define the delegate signature
SiegeMessageDelegate: TypeAlias = Callable[[UserId, Username, Channel, Message], Awaitable[Response]]


class SiegeListener:
    """
    Discord message listener for siege-related commands and interactions.
    
    This class handles incoming Discord messages and provides automated
    responses for siege assignment queries and commands.
    """
    
    def __init__(self, discord_api: DiscordAPI, guild_name: str, input_handler: Optional[Callable[[str, str, str, str], Awaitable[str]]] = None) -> None:
        """
        Initialize the siege listener.
        
        Args:
            discord_api: The Discord API client instance.
            guild_name: The name of the Discord guild to monitor.
            input_handler: Optional callback function to handle message input processing.
                          Signature: async def handler(user_id: str, username: str, channel: str, message: str) -> str
        """
        self.discord_api = discord_api
        self.guild_name = guild_name
        self.input_handler = input_handler
        self.channel_name: Optional[str] = None
    
    async def bind_to_channel(self, channel_name: str) -> None:
        """
        Bind message listener to a single specified channel.
        
        Args:
            channel_name: Name of the channel to monitor.
        """
        try:
            await self.discord_api.bind_channel_listener(
                self.guild_name,
                channel_name,
                self._on_message
            )
            self.channel_name = channel_name
            logger.info(f"Siege listener bound to channel '{channel_name}' in guild: {self.guild_name}")
        except Exception as e:
            logger.error(f"Error binding to channel {channel_name}: {e}")
            raise
    
    async def unbind_listener(self) -> None:
        """
        Unbind message listener from the current channel.
        """
        try:
            if self.channel_name:
                await self.discord_api.unbind_channel_listener(
                    self.guild_name,
                    self.channel_name
                )
                logger.info(f"Siege listener unbound from channel '{self.channel_name}' in guild: {self.guild_name}")
                self.channel_name = None
            else:
                logger.warning("No channel currently bound")
        except Exception as e:
            logger.error(f"Error unbinding listener: {e}")
            raise
    
    async def _on_message(self, message: discord.Message) -> None:
        """
        Handle incoming Discord messages.
        
        Args:
            message: The Discord message object.
        """
        # Ignore messages from bots
        if message.author.bot:
            return
        
        try:
            # Extract message details
            user_id = str(message.author.id)
            username = message.author.display_name or message.author.name
            channel = message.channel.name if hasattr(message.channel, 'name') else 'DM'
            content = message.content.strip()
            
            # Invoke the input handler if provided
            if self.input_handler:
                response = await self.input_handler(user_id, username, channel, content)
                
                # Send response if provided
                if response:
                    await message.channel.send(response)
            else:
                logger.debug(f"No input handler configured for message from {username}: {content}")
                
        except Exception as e:
            logger.error(f"Error processing message from {message.author}: {e}")
            try:
                await message.channel.send("Sorry, I encountered an error processing your message.")
            except Exception as send_error:
                logger.error(f"Failed to send error response: {send_error}")
    
    def set_input_handler(self, handler: SiegeMessageDelegate) -> None:
        """
        Set the input handler function.
        
        Args:
            handler: Async function to handle message input processing.
                    Signature: async def handler(user_id: str, username: str, channel: str, message: str) -> str
        """
        self.input_handler = handler


async def create_siege_listener(discord_api: DiscordAPI, guild_name: str, channel_name: str, input_handler: SiegeMessageDelegate) -> SiegeListener:
    """
    Create and initialize a siege listener.
    
    Args:
        discord_api: The Discord API client instance.
        guild_name: The name of the Discord guild to monitor.
        channel_name: The name of the channel to bind to.
        input_handler: Optional callback function to handle message input processing. 
                      Defaults to OnSiegeChannelMessage if not provided.
    
    Returns:
        Initialized SiegeListener instance.
    """
    listener = SiegeListener(discord_api, guild_name, input_handler)
    await listener.bind_to_channel(channel_name)
    return listener
