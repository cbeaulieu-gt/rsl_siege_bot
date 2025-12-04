# clan/calendar.py

"""
Provides a Calendar class for event scheduling logic based on event type and frequency.
"""
import datetime
from pathlib import Path
from typing import Optional, Dict

from clan.events import Event, load_event_config

class Calendar:
    """
    Calendar for determining if an event is active on a given date.
    Supports weekly and bi-weekly scheduling with a configurable start week per event.
    """

    def __init__(self, event_frequencies: Dict[Event, str], start_weeks: Optional[Dict[Event, int]] = None) -> None:
        """
        Initialize the Calendar.

        Args:
            event_frequencies (Dict[Event, str]): Mapping of Event to frequency ("weekly" or "biweekly").
            start_weeks (Optional[Dict[Event, int]]): Mapping of Event to ISO week number to start bi-weekly events.
        """
        self.event_frequencies = event_frequencies
        self.start_weeks = start_weeks or {}

    def is_event_week(self, event: Event, date: Optional[datetime.date] = None) -> bool:
        """
        Check if the event is active on the given date.

        Args:
            event (Event): The event to check.
            date (Optional[datetime.date]): The date to check. Uses today if not provided.

        Returns:
            bool: True if the event is active, False otherwise.

        Raises:
            ValueError: If frequency is unsupported or required start_week is missing.
        """
        check_date = date or datetime.date.today()
        frequency = self.event_frequencies.get(event, "weekly")
        if frequency == "weekly":
            return True
        if frequency == "biweekly":
            start_week = self.start_weeks.get(event)
            if start_week is None:
                raise ValueError(f"start_week must be set for biweekly event: {event.name}")
            current_week = check_date.isocalendar().week
            return (current_week - start_week) % 2 == 0
        raise ValueError(f"Unsupported frequency: {frequency} for event: {event.name}")

    @classmethod
    def from_config(cls, config_path: str) -> "Calendar":
        """
        Create a Calendar instance from a configuration file.

        Args:
            config_path (str): Path to the configuration file.

        Returns:
            Calendar: A new Calendar instance with event data loaded from the config.

        Raises:
            FileNotFoundError: If the config file does not exist.
            ValueError: If the config file is invalid or missing required fields.
        """
        event_mappings  = load_event_config(Path(config_path))
        return cls(event_frequencies=event_mappings[0], start_weeks=event_mappings[1])