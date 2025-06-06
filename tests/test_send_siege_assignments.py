"""
Unit tests for send_siege_assignments and send_siege_assignment_dm in siege.py.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from siege.siege import send_siege_assignments, send_siege_assignment_dm

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
    assignments = {'old': [], 'new': ['Tower 1'], 'unchanged': []}
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
    assert "Reserve Status: Yes" in args[1]
    assert "Attack Day: 2" in args[1]
    assert "ASSIGNMENT TABLE" in args[1]

@pytest.mark.asyncio
async def test_send_siege_assignments_calls_dm(monkeypatch):
    """
    Test that send_siege_assignments calls send_siege_assignment_dm with correct reserve/attack info.
    """
    # Setup
    discord_client = DummyDiscordClient()
    changed_assignments = {"Alice": ([], ["Tower 1"])}
    unchanged_assignments = {"Bob": ["Tower 2"]}
    siege_date = "2025-06-05"
    siege_assignments = [
        type("SA", (), {"name": "Alice", "set_reserve": True, "attack_day": 1})(),
        type("SA", (), {"name": "Bob", "set_reserve": False, "attack_day": 2})(),
    ]
    # Patch send_siege_assignment_dm to record calls
    called = {}
    async def fake_send_dm(dc, member_obj, assignments, siege_date, reserve_status=None, attack_day=None):
        called[member_obj.name] = (reserve_status, attack_day)
    monkeypatch.setattr("siege.siege.send_siege_assignment_dm", fake_send_dm)
    # Patch find_discord_member to match by name
    monkeypatch.setattr("siege.siege.find_discord_member", lambda members, name: next((m for m in members if m.name == name), None))
    # Patch asyncio.sleep to skip delay
    monkeypatch.setattr("asyncio.sleep", lambda s: None)
    # Run
    send_all = send_siege_assignments(
        discord_client,
        changed_assignments,
        unchanged_assignments,
        siege_date,
        send_dm=True,
        siege_assignments=siege_assignments
    )
    await send_all()
    # Check
    assert called["Alice"] == (True, 1)
    assert called["Bob"] == (False, 2)
