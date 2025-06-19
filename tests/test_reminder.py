"""
Unit tests for the Reminder class in clan_reminders.py.
"""
import datetime
import configparser
import pytest
from unittest.mock import MagicMock
from clan.clan_reminders import Reminder

class DummyDiscordClient:
    def __init__(self, guild_id):
        self.guild_id = guild_id

@pytest.fixture
def base_config():
    config = configparser.ConfigParser()
    config["Reminders"] = {"hydra": "1", "chimera": "2"}
    config["ReminderTimes"] = {"hydra": "7", "chimera": "12"}
    config["RemindersSent"] = {}
    return config

@pytest.fixture
def dummy_client():
    return DummyDiscordClient(guild_id="1234567890")

@pytest.mark.parametrize("event_name,reminder_day,utc_time,weekday,hour,already_sent,expected", [
    ("hydra", 1, 7, 1, 8, False, True),   # Correct day, after hour
    ("hydra", 1, 7, 1, 6, False, False),  # Correct day, before hour
    ("hydra", 1, 7, 2, 8, False, False),  # Wrong day
    ("hydra", 1, 7, 1, 8, True, False),   # Already sent
    ("chimera", 2, 12, 2, 13, False, True),
    ("chimera", 2, 12, 2, 11, False, False),
])
def test_should_send(event_name, reminder_day, utc_time, weekday, hour, already_sent, expected, base_config, dummy_client, monkeypatch):
    reminder = Reminder(event_name, reminder_day, dummy_client, send_func=None, utc_time=utc_time)
    config = base_config
    day = datetime.date(2025, 6, 16)  # Monday
    # Set the weekday to match the test
    test_day = day + datetime.timedelta(days=(weekday - day.weekday()))
    # Set already sent if needed
    sent_key = f"{dummy_client.guild_id}_{event_name}Sent"
    if already_sent:
        config["RemindersSent"][sent_key] = str(test_day)
    # Patch datetime.datetime.utcnow
    class FakeDateTime(datetime.datetime):
        @classmethod
        def utcnow(cls):
            return datetime.datetime(2025, 6, 16, hour, 0, 0)
    monkeypatch.setattr(datetime, "datetime", FakeDateTime)
    assert reminder.should_send(test_day, config) == expected

def test_clear_reminder(base_config, dummy_client):
    reminder = Reminder("hydra", 1, dummy_client, send_func=None, utc_time=7)
    config = base_config
    day = datetime.date(2025, 6, 16)
    sent_key = f"{dummy_client.guild_id}_hydraSent"
    config["RemindersSent"][sent_key] = str(day)
    reminder.clear(config)
    assert sent_key not in config["RemindersSent"]

@pytest.mark.asyncio
def test_send_sets_sent_flag(base_config, dummy_client):
    called = {}
    async def fake_send_func(client):
        called["sent"] = True
    reminder = Reminder("hydra", 1, dummy_client, send_func=fake_send_func, utc_time=7)
    config = base_config
    day = datetime.date(2025, 6, 16)
    sent_key = f"{dummy_client.guild_id}_hydraSent"
    assert sent_key not in config["RemindersSent"]
    import asyncio
    asyncio.run(reminder.send(day, config))
    assert sent_key in config["RemindersSent"]
    assert called["sent"] is True
