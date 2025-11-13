"""
Unit tests for the ReminderSentStore utility class (JSON version).
"""
import os
import tempfile
import pytest
from clan.reminder_sent_store import ReminderSentStore

def test_store_set_and_get(tmp_path, monkeypatch):
    monkeypatch.setenv('APPDATA', str(tmp_path))
    store = ReminderSentStore(app_name="test_siege_reminders", filename="test_reminders_sent.json")
    guild_id = "guild1"
    reminder_type = "hydra"
    value = "2025-06-20"
    store.set(guild_id, reminder_type, value)
    assert store.get(guild_id, reminder_type) == value


def test_store_clear(tmp_path, monkeypatch):
    monkeypatch.setenv('APPDATA', str(tmp_path))
    store = ReminderSentStore(app_name="test_siege_reminders", filename="test_reminders_sent.json")
    guild_id = "guild1"
    reminder_type = "hydra"
    value = "2025-06-20"
    store.set(guild_id, reminder_type, value)
    store.clear(guild_id, reminder_type)
    assert store.get(guild_id, reminder_type) is None


def test_store_clear_all(tmp_path, monkeypatch):
    monkeypatch.setenv('APPDATA', str(tmp_path))
    store = ReminderSentStore(app_name="test_siege_reminders", filename="test_reminders_sent.json")
    store.set("guild1", "hydra", "2025-06-20")
    store.set("guild2", "chimera", "2025-06-21")
    store.clear_all()
    assert store.get("guild1", "hydra") is None
    assert store.get("guild2", "chimera") is None


def test_store_persistence(tmp_path, monkeypatch):
    monkeypatch.setenv('APPDATA', str(tmp_path))
    app_name = "test_siege_reminders"
    filename = "test_reminders_sent.json"
    guild_id = "guild1"
    reminder_type = "hydra"
    value = "2025-06-20"
    # Set value and reload
    store = ReminderSentStore(app_name=app_name, filename=filename)
    store.set(guild_id, reminder_type, value)
    # Create a new instance to check persistence
    store2 = ReminderSentStore(app_name=app_name, filename=filename)
    assert store2.get(guild_id, reminder_type) == value
