import os
import json
from pathlib import Path
from typing import Optional
import threading

class ReminderSentStore:
    """
    Utility class to store and retrieve RemindersSent values in a JSON file in the user's appData folder.
    Structure: { guild_id: { reminder_type: last_sent_day, ... }, ... }
    Thread-safe singleton for file access.
    """
    _lock = threading.RLock()
    _data = None
    _file_path = None

    def __init__(self, app_name: str = "siege_reminders", filename: str = "reminders_sent.json"):
        self.app_name = app_name
        self.filename = filename
        if self.__class__._file_path is None:
            self.__class__._file_path = self._get_appdata_file_path()
        if self.__class__._data is None:
            self.__class__._data = self._load()

    @property
    def file_path(self) -> str:
        return self.__class__._file_path

    def _get_appdata_file_path(self) -> str:
        appdata = os.getenv('APPDATA') or os.path.expanduser('~/.config')
        app_dir = Path(appdata) / self.app_name
        app_dir.mkdir(parents=True, exist_ok=True)
        return str(app_dir / self.filename)

    def _load(self):
        with self.__class__._lock:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as f:
                    try:
                        return json.load(f)
                    except Exception:
                        return {}
            return {}

    def _save(self):
        with self.__class__._lock:
            with open(self.file_path, 'w') as f:
                json.dump(self.__class__._data, f, indent=2)

    def get(self, guild_id: str, reminder_type: str) -> Optional[str]:
        with self.__class__._lock:
            return self.__class__._data.get(guild_id, {}).get(reminder_type)

    def set(self, guild_id: str, reminder_type: str, value: str) -> None:
        with self.__class__._lock:
            if guild_id not in self.__class__._data:
                self.__class__._data[guild_id] = {}
            self.__class__._data[guild_id][reminder_type] = value
            self._save()

    def clear(self, guild_id: str, reminder_type: str) -> None:
        with self.__class__._lock:
            if guild_id in self.__class__._data and reminder_type in self.__class__._data[guild_id]:
                del self.__class__._data[guild_id][reminder_type]
                if not self.__class__._data[guild_id]:
                    del self.__class__._data[guild_id]
                self._save()

    def clear_all(self):
        with self.__class__._lock:
            self.__class__._data = {}
            self._save()
