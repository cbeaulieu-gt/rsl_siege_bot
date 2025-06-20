"""
Test concurrent ReminderSentStore usage with multiple Reminder instances.
"""
import pytest
import threading
import time
import json
from clan.reminder_sent_store import ReminderSentStore
from pathlib import Path

@pytest.mark.timeout(10)
def test_concurrent_reminder_instances(tmp_path, monkeypatch):
    monkeypatch.setenv('APPDATA', str(tmp_path))
    app_name = "test_siege_reminders"
    filename = "test_reminders_sent.json"
    store = ReminderSentStore(app_name=app_name, filename=filename)
    guild_id1 = "guild1"
    guild_id2 = "guild2"
    reminder_type1 = "hydra"
    reminder_type2 = "chimera"
    value1 = "2025-06-20"
    value2 = "2025-06-21"

    def writer1():
        store.set(guild_id1, reminder_type1, value1)

    def writer2():
        store.set(guild_id2, reminder_type2, value2)

    t1 = threading.Thread(target=writer1)
    t2 = threading.Thread(target=writer2)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Read the file directly to verify both entries exist
    file_path = Path(tmp_path) / app_name / filename
    with open(file_path, 'r') as f:
        data = json.load(f)
    assert guild_id1 in data
    assert guild_id2 in data
    assert data[guild_id1][reminder_type1] == value1
    assert data[guild_id2][reminder_type2] == value2
