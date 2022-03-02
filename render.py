from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any

from events import DataLevelBoundaries

"""Provides a type alias for a mapping between dates and the associated activity level."""
DataLevelMap = dict[datetime, int]

# mapping of characters to the data level which should be in the 5 bit space available for weekdays
CHARACTERS_5_BIT: dict[str, tuple[int]] = {
    "A": (0, 4, 4, 4, 4, 4, 0,
          0, 4, 0, 0, 4, 0, 0,
          0, 4, 4, 4, 4, 4, 0),

    "B": (0, 4, 4, 4, 4, 4, 0,
          0, 4, 0, 4, 0, 4, 0,
          0, 0, 4, 4, 4, 0, 0),

    "C": (0, 4, 4, 4, 4, 4, 0,
          0, 4, 0, 0, 0, 4, 0,
          0, 4, 4, 0, 4, 4, 0),

    "D": (0, 4, 4, 4, 4, 4, 0,
          0, 4, 0, 0, 0, 4, 0,
          0, 0, 4, 4, 4, 0, 0),

    "E": (0, 4, 4, 4, 4, 4, 0,
          0, 4, 0, 4, 0, 4, 0,
          0, 4, 0, 0, 0, 4, 0),

    "F": (0, 4, 4, 4, 4, 4, 0,
          0, 4, 0, 4, 0, 0, 0,
          0, 4, 0, 0, 0, 0, 0),

    "G": (0, 4, 4, 4, 4, 4, 0,
          0, 4, 0, 0, 0, 4, 0,
          0, 4, 0, 4, 4, 4, 0),

    "H": (0, 4, 4, 4, 4, 4, 0,
          0, 0, 0, 4, 0, 0, 0,
          0, 4, 4, 4, 4, 4, 0),

    "I": (0, 4, 0, 0, 0, 4, 0,
          0, 4, 4, 4, 4, 4, 0,
          0, 4, 0, 0, 0, 4, 0),

    "J": (0, 4, 0, 0, 4, 4, 0,
          0, 4, 0, 0, 0, 4, 0,
          0, 4, 4, 4, 4, 4, 0),

    "K": (0, 4, 4, 4, 4, 4, 0,
          0, 0, 0, 4, 0, 0, 0,
          0, 4, 4, 0, 4, 4, 0),

    "L": (0, 4, 4, 4, 4, 4, 0,
          0, 0, 0, 0, 0, 4, 0,
          0, 0, 0, 0, 0, 4, 0),

    "M": (0, 4, 4, 4, 4, 4, 0,
          0, 0, 4, 4, 0, 0, 0,
          0, 4, 4, 4, 4, 4, 0),

    "N": (0, 4, 4, 4, 4, 4, 0,
          0, 0, 4, 4, 4, 0, 0,
          0, 4, 4, 4, 4, 4, 0),

    "O": (0, 4, 4, 4, 4, 4, 0,
          0, 4, 0, 0, 0, 4, 0,
          0, 4, 4, 4, 4, 4, 0),

    "P": (0, 4, 4, 4, 4, 4, 0,
          0, 4, 0, 4, 0, 0, 0,
          0, 4, 4, 4, 0, 0, 0),

    "Q": (0, 4, 4, 4, 4, 0, 0,
          0, 4, 0, 0, 4, 4, 0,
          0, 4, 4, 4, 4, 4, 0),

    "R": (0, 4, 4, 4, 4, 4, 0,
          0, 4, 0, 4, 0, 0, 0,
          0, 4, 4, 0, 4, 4, 0),

    "S": (0, 4, 4, 4, 0, 4, 0,
          0, 4, 0, 4, 0, 4, 0,
          0, 4, 0, 4, 4, 4, 0),

    "T": (0, 4, 0, 0, 0, 0, 0,
          0, 4, 4, 4, 4, 4, 0,
          0, 4, 0, 0, 0, 0, 0),

    "U": (0, 4, 4, 4, 4, 4, 0,
          0, 0, 0, 0, 0, 4, 0,
          0, 4, 4, 4, 4, 4, 0),

    "V": (0, 4, 4, 4, 4, 0, 0,
          0, 0, 0, 0, 0, 4, 0,
          0, 4, 4, 4, 4, 0, 0),

    "W": (0, 4, 4, 4, 4, 4, 0,
          0, 0, 0, 4, 4, 0, 0,
          0, 4, 4, 4, 4, 4, 0),

    "X": (0, 4, 4, 0, 4, 4, 0,
          0, 0, 0, 4, 0, 0, 0,
          0, 4, 4, 0, 4, 4, 0),

    "Y": (0, 4, 4, 4, 0, 0, 0,
          0, 0, 0, 4, 4, 4, 0,
          0, 4, 4, 4, 0, 0, 0),

    "Z": (0, 4, 0, 0, 4, 4, 0,
          0, 4, 0, 4, 0, 4, 0,
          0, 4, 4, 0, 0, 4, 0),

    "0": (0, 4, 4, 4, 4, 4, 0,
          0, 4, 0, 0, 0, 4, 0,
          0, 4, 4, 4, 4, 4, 0),

    "1": (0, 4, 0, 0, 0, 4, 0,
          0, 4, 4, 4, 4, 4, 0,
          0, 0, 0, 0, 0, 4, 0),

    "2": (0, 4, 0, 4, 4, 4, 0,
          0, 4, 0, 4, 0, 4, 0,
          0, 4, 4, 4, 0, 4, 0),

    "3": (0, 4, 0, 0, 0, 4, 0,
          0, 4, 0, 4, 0, 4, 0,
          0, 4, 4, 4, 4, 4, 0),

    "4": (0, 4, 4, 4, 0, 0, 0,
          0, 0, 0, 4, 0, 0, 0,
          0, 4, 4, 4, 4, 4, 0),

    "5": (0, 4, 4, 4, 0, 4, 0,
          0, 4, 0, 4, 0, 4, 0,
          0, 4, 0, 4, 4, 4, 0),

    "6": (0, 4, 4, 4, 4, 4, 0,
          0, 4, 0, 4, 0, 4, 0,
          0, 4, 0, 4, 4, 4, 0),

    "7": (0, 4, 0, 0, 0, 0, 0,
          0, 4, 0, 4, 4, 4, 0,
          0, 4, 4, 0, 0, 0, 0),

    "8": (0, 4, 4, 4, 4, 4, 0,
          0, 4, 0, 4, 0, 4, 0,
          0, 4, 4, 4, 4, 4, 0),

    "9": (0, 4, 4, 4, 0, 0, 0,
          0, 4, 0, 4, 0, 0, 0,
          0, 4, 4, 4, 4, 4, 0),

    "?": (0, 4, 0, 0, 0, 0, 0,
          0, 4, 0, 4, 0, 4, 0,
          0, 0, 4, 0, 0, 0, 0),

    "!": (0, 0, 0, 0, 0, 0, 0,
          0, 4, 4, 4, 0, 4, 0,
          0, 0, 0, 0, 0, 0, 0),

    "_": (0, 0, 0, 0, 0, 4, 0,
          0, 0, 0, 0, 0, 4, 0,
          0, 0, 0, 0, 0, 4, 0),

    "+": (0, 0, 4, 0, 0, 0, 4,
          4, 4, 0, 0, 0, 4, 0,
          0, 0, 0, 0, 0, 0, 0),

    "-": (0, 0, 0, 0, 0, 0, 4,
          4, 4, 0, 0, 0, 0, 0,
          0, 0, 0, 0, 0, 0, 0),

    "%": (0, 4, 0, 0, 4, 4, 0,
          0, 0, 0, 4, 0, 0, 0,
          0, 4, 4, 0, 0, 4, 0),

    "(": (0, 0, 4, 4, 4, 0, 0,
          0, 4, 0, 0, 0, 4, 0,
          0, 4, 0, 0, 0, 4, 0),

    ")": (0, 4, 0, 0, 0, 4, 0,
          0, 4, 0, 0, 0, 4, 0,
          0, 0, 4, 4, 4, 0, 0),

    "{": (0, 0, 0, 4, 0, 0, 0,
          0, 4, 4, 0, 4, 4, 0,
          0, 4, 0, 0, 0, 4, 0),

    "}": (0, 4, 0, 0, 0, 4, 0,
          0, 4, 4, 0, 4, 4, 0,
          0, 0, 0, 4, 0, 0, 0),

    "=": (0, 0, 4, 0, 4, 0, 0,
          0, 0, 4, 0, 4, 0, 0,
          0, 0, 4, 0, 4, 0, 0),

    "<": (0, 0, 0, 4, 0, 0, 0,
          0, 0, 4, 0, 4, 0, 0,
          0, 0, 4, 0, 4, 0, 0),

    ">": (0, 0, 4, 0, 4, 0, 0,
          0, 0, 4, 0, 4, 0, 0,
          0, 0, 0, 4, 0, 0, 0),

    "^": (0, 0, 4, 0, 0, 0, 0,
          4, 0, 0, 0, 0, 0, 0,
          4, 0, 0, 0, 0, 0, 0),

    " ": (0, 0, 0, 0, 0, 0, 0,
          0, 0, 0, 0, 0, 0, 0,
          0, 0, 0, 0, 0, 0, 0),

    ":": (0, 0, 0, 0, 0, 0, 0,
          0, 0, 3, 0, 4, 0, 0,
          0, 0, 0, 0, 0, 0, 0),
}


def scale_data_level_map(boundaries: DataLevelBoundaries, data_level_map: DataLevelMap) -> DataLevelMap:
    """Scale the given data map levels to the given boundaries."""
    return {date: boundaries[data_level] for date, data_level in data_level_map.items()}


def get_last_week_end() -> datetime:
    """Retrieve the date of the most recent saturday where we can start adding commit activity."""
    now = datetime.now()

    return now - timedelta(days=(now.isoweekday() + 1) % 7)


class RendererBase(ABC):
    """Base class for all DataLevelMap renders."""

    @abstractmethod
    def render(self, obj: Any, starting_date: datetime) -> DataLevelMap:
        """The render method should accept an object and return a DataLevelMap representative of that object."""


class TextRenderer(RendererBase):
    def render(self, obj: Any, starting_date: datetime = get_last_week_end()) -> DataLevelMap:
        if not isinstance(obj, str):
            raise TypeError(f"TextRenderer can not render object of type '{type(obj)}'")

        date = get_last_week_end()
        data_level_map = dict()

        for c in obj:
            try:
                data_levels = CHARACTERS_5_BIT[c]
            except KeyError:
                raise ValueError(f"character '{c}' cannot be rendered")

            for data_level in data_levels[::-1]:  # todo: this reverse might not be necessary
                data_level_map[date] = data_level
                date -= timedelta(days=1)

            for _ in range(7):
                data_level_map[date] = 0
                date -= timedelta(days=1)

        return data_level_map
