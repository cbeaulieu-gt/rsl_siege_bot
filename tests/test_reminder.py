"""
Unit tests for the Reminder class in clan_reminders.py.
"""
import datetime
import configparser
import pytest
from unittest.mock import MagicMock
from clan.clan_reminders import Reminder
from clan.reminder_sent_store import ReminderSentStore

class DummyDiscordClient:
    def __init__(self, guild_id):
        self.guild_id = guild_id

@pytest.fixture
def base_config():
    config = configparser.ConfigParser()
    config["Reminders"] = {"hydra": "1", "chimera": "2"}
    config["ReminderTimes"] = {"hydra": "7", "chimera": "12"}
    config["Channels"] = {"reminders": "general"}
    return config

@pytest.fixture
def dummy_client():
    return DummyDiscordClient(guild_id="1234567890")

@pytest.fixture
def dummy_store(tmp_path, monkeypatch):
    monkeypatch.setenv('APPDATA', str(tmp_path))
    return ReminderSentStore(app_name="test_siege_reminders", filename="test_reminders_sent.ini")

@pytest.mark.parametrize("event_name,reminder_day,utc_time,weekday,hour,already_sent,expected", [
    ("hydra", 1, 7, 1, 8, False, True),   # Correct day, after hour
    ("hydra", 1, 7, 1, 6, False, False),  # Correct day, before hour
    ("hydra", 1, 7, 2, 8, False, False),  # Wrong day
    ("hydra", 1, 7, 1, 8, True, False),   # Already sent
    ("chimera", 2, 12, 2, 13, False, True),
    ("chimera", 2, 12, 2, 11, False, False),
])
def test_should_send(event_name, reminder_day, utc_time, weekday, hour, already_sent, expected, base_config, dummy_client, dummy_store, monkeypatch):
    reminder = Reminder(event_name, reminder_day, dummy_client, send_func=None, utc_time=utc_time, sent_store=dummy_store)
    config = base_config
    day = datetime.date(2025, 6, 16)  # Monday
    # Set the weekday to match the test
    test_day = day + datetime.timedelta(days=(weekday - day.weekday()))
    # Set already sent if needed
    if already_sent:
        dummy_store.set(dummy_client.guild_id, event_name, str(test_day))
    # Patch datetime.datetime.utcnow
    class FakeDateTime(datetime.datetime):
        @classmethod
        def utcnow(cls):
            return datetime.datetime(2025, 6, 16, hour, 0, 0)
    monkeypatch.setattr(datetime, "datetime", FakeDateTime)
    assert reminder.should_send(test_day) == expected

def test_clear_reminder(base_config, dummy_client, dummy_store):
    reminder = Reminder("hydra", 1, dummy_client, send_func=None, utc_time=7, sent_store=dummy_store)
    day = datetime.date(2025, 6, 16)
    dummy_store.set(dummy_client.guild_id, "hydra", str(day))
    reminder.clear()
    assert dummy_store.get(dummy_client.guild_id, "hydra") is None

def test_send_sets_sent_flag(base_config, dummy_client, dummy_store):
    called = {}
    async def fake_send_func(client, channel):
        called["sent"] = True
    reminder = Reminder("hydra", 1, dummy_client, send_func=fake_send_func, utc_time=7, sent_store=dummy_store)
    day = datetime.date(2025, 6, 16)
    assert dummy_store.get(dummy_client.guild_id, "hydra") is None
    import asyncio
    asyncio.run(reminder.send(day))
    assert dummy_store.get(dummy_client.guild_id, "hydra") == str(day)
    assert called["sent"] is True
