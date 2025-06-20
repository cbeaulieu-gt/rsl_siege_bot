import os
import json
from pathlib import Path
from typing import Optional

class ReminderSentStore:
    """
    Utility class to store and retrieve RemindersSent values in a JSON file in the user's appData folder.
    Structure: { guild_id: { reminder_type: last_sent_day, ... }, ... }
    """
    def __init__(self, app_name: str = "siege_reminders", filename: str = "reminders_sent.json"):
        self.app_name = app_name
        self.filename = filename
        self.file_path = self._get_appdata_file_path()
        self._data = self._load()

    def _get_appdata_file_path(self) -> str:
        appdata = os.getenv('APPDATA') or os.path.expanduser('~/.config')
        app_dir = Path(appdata) / self.app_name
        app_dir.mkdir(parents=True, exist_ok=True)
        return str(app_dir / self.filename)

    def _load(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                try:
                    return json.load(f)
                except Exception:
                    return {}
        return {}

    def _save(self):
        with open(self.file_path, 'w') as f:
            json.dump(self._data, f, indent=2)

    def get(self, guild_id: str, reminder_type: str) -> Optional[str]:
        return self._data.get(guild_id, {}).get(reminder_type)

    def set(self, guild_id: str, reminder_type: str, value: str) -> None:
        if guild_id not in self._data:
            self._data[guild_id] = {}
        self._data[guild_id][reminder_type] = value
        self._save()

    def clear(self, guild_id: str, reminder_type: str) -> None:
        if guild_id in self._data and reminder_type in self._data[guild_id]:
            del self._data[guild_id][reminder_type]
            if not self._data[guild_id]:
                del self._data[guild_id]
            self._save()

    def clear_all(self):
        self._data = {}
        self._save()
