"""
Defines the Event enumeration for supported clan events.
"""
from configparser import ConfigParser
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Tuple


class Event(Enum):
    """
    Enumeration of supported clan events.
    """
    SIEGE = auto()
    HYDRA_CLASH = auto()
    CHIMERA_CLASH = auto()

EVENT_FREQUENCIES_SECTION = "EventFrequencies"
EVENT_START_WEEK_SECTION = "EventStartWeek"
EVENT_NAME_MAP = {
    "siege": Event.SIEGE,
    "hydra": Event.HYDRA_CLASH,
    "chimera": Event.CHIMERA_CLASH,
}

def get_event(name: str) -> Event:
    """
    Get the Event enum member corresponding to the given event name.

    Args:
        name (str): The name of the event (case-insensitive).

    Returns:
        Event: The corresponding Event enum member.

    Raises:
        KeyError: If the event name is not recognized.
    """
    event = EVENT_NAME_MAP.get(name.strip().lower())
    if event is None:
        raise KeyError(f"Unknown event name: {name}")
    return event

def load_event_config(config_path: Path) -> Tuple[Dict[Event, str], Dict[Event, int]]:
    """
    Load event frequencies and start weeks from the configuration file.

    Args:
        config_path (Path): Path to the guild_config.ini file.

    Returns:
        Tuple[Dict[Event, str], Dict[Event, int]]:
            - Mapping of Event to frequency ("weekly" or "biweekly").
            - Mapping of Event to start week (ISO week number).

    Raises:
        KeyError: If an event name in the config is not recognized.
        ValueError: If start week format is invalid.
    """
    parser = ConfigParser()
    parser.read(config_path)

    event_frequencies: Dict[Event, str] = {}
    start_weeks: Dict[Event, int] = {}

    if parser.has_section(EVENT_FREQUENCIES_SECTION):
        for name, freq in parser.items(EVENT_FREQUENCIES_SECTION):
            event = EVENT_NAME_MAP.get(name.strip().lower())
            if event is None:
                raise KeyError(f"Unknown event name in config: {name}")
            event_frequencies[event] = freq.strip().lower()

    if parser.has_section(EVENT_START_WEEK_SECTION):
        for name, week_str in parser.items(EVENT_START_WEEK_SECTION):
            event = EVENT_NAME_MAP.get(name.strip().lower())
            if event is None:
                raise KeyError(f"Unknown event name in config: {name}")
            # Accept formats like "202450" (year+week) or just "50"
            try:
                if len(week_str) == 6 and week_str.isdigit():
                    week_num = int(week_str[-2:])
                elif week_str.isdigit():
                    week_num = int(week_str)
                else:
                    raise ValueError
            except ValueError:
                raise ValueError(f"Invalid start week format for {name}: {week_str}")
            start_weeks[event] = week_num

    return event_frequencies, start_weeks