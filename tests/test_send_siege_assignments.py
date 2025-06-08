"""
Unit tests for send_siege_assignments and send_siege_assignment_dm in siege.py.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from siege.siege import send_siege_assignments, send_siege_assignment_dm
from excel import Position

class DummyDiscordClient:
    async def get_guild_members_disc(self):
        return [MagicMock(name="Alice", nick="Alice"), MagicMock(name="Bob", nick="Bob")]
    async def send_message(self, member_obj, message):
        return f"Sent to {getattr(member_obj, 'name', '')}: {message}"

def test_send_siege_assignment_dm_includes_reserve_and_attack_day():
    """
    Test that send_siege_assignment_dm includes reserve status and attack day in the DM message.
    """
    discord_client = MagicMock()
    member_obj = MagicMock()
    assignments = {'old': [], 'new': [Position("Defense Tower", 1, 1, 1)], 'unchanged': []}
    siege_date = "2025-06-05"
    reserve_status = True
    attack_day = 2
    # Patch format_assignment_table to a known value
    import siege.siege
    siege.siege.format_assignment_table = lambda old, new, unchanged: "ASSIGNMENT TABLE"
    result = send_siege_assignment_dm(
        discord_client,
        member_obj,
        assignments,
        siege_date,
        set_reserve=reserve_status,
        attack_day=attack_day
    )
    # Check that reserve and attack day info is in the message
    args, kwargs = discord_client.send_message.call_args
    assert "Have Reserve Set:** Yes" in args[1]
    assert "Attack Day:** 2" in args[1]
    assert "Set At" in args[1]