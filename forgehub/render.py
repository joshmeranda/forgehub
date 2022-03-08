from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Optional

from forgehub.events import DataLevelBoundaries

__all__ = [
    "DataLevelMap",
    "get_last_week_end",
    "RendererBase",
    "TextRenderer",
]


class DataLevelMap:
    def __init__(self):
        """Provides mapping between dates and their data levels."""
        self.__date_to_data_level: dict[datetime, int] = dict()

    def __setitem__(self, key: datetime, value: int):
        self.__date_to_data_level[key] = value

    def __getitem__(self, item: datetime):
        return self.__date_to_data_level[item]

    def __str__(self):
        calendar = [[] for i in range(7)]
        sorted_data_levels = [
            data_level
            for _, data_level in sorted(
                self.__date_to_data_level.items(), key=lambda pair: pair[0]
            )
        ]

        while True:
            try:
                for i in range(len(calendar)):
                    match sorted_data_levels.pop(0):
                        case 0:
                            c = " "
                        case 1:
                            c = "-"
                        case 2:
                            c = "="
                        case 3:
                            c = "H"
                        case 4:
                            c = "#"
                        case n:
                            raise ValueError(f"invalid data level '{n}'")

                    calendar[i].append(c)
            except IndexError:
                break

        return "\n".join(["".join(i) for i in calendar])

    def items(self) -> list[(datetime, int)]:
        """Analogous to the dictionary items method retrieving dates and their data levels.

        :return: A list of tuples with a datetime and int.
        """
        return list(self.__date_to_data_level.items())

    def scale_to_boundaries(self, boundaries: DataLevelBoundaries):
        """Scale the `DataLevelMap`'s stored levels to the given boundaries."""
        self.__date_to_data_level = {
            date: boundaries[data_level]
            for date, data_level in self.__date_to_data_level.items()
        }


# mapping of characters to the data level which should be in the 5 bit space available for weekdays
# fmt: off
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
# fmt: on


def get_last_week_end() -> datetime:
    """Retrieve the date of the most recent saturday where we can start adding commit activity."""
    now = datetime.now()

    return now - timedelta(days=(now.isoweekday() + 1) % 7)


class RendererBase(ABC):
    """Base class for all DataLevelMap renders."""

    @abstractmethod
    def render(self, obj: Any, end_date: datetime) -> DataLevelMap:
        """The render method should accept an object and return a DataLevelMap representative of that object.

        :param obj: The object to render.
        :param end_date: The last day a data level can occur on .
        """

    def render_data_levels(
        self, data_levels: list[int], end_date: Optional[datetime] = None
    ) -> DataLevelMap:
        """Map each data level to the corresponding date.

        :param data_levels: The data levels to render.
        :param end_date: The last day a data level can occur on.
        """

        date = end_date if end_date is not None else get_last_week_end()
        data_level_map = DataLevelMap()

        for data_level in reversed(data_levels):
            data_level_map[date] = data_level
            date -= timedelta(days=1)

        return data_level_map


class TextRenderer(RendererBase):
    def render(self, obj: Any, end_date: Optional[datetime] = None) -> DataLevelMap:
        if not isinstance(obj, str):
            raise TypeError(f"TextRenderer can not render object of type '{type(obj)}'")

        date = end_date if end_date is not None else get_last_week_end()
        data_level_map = DataLevelMap()

        for c in reversed(obj):
            try:
                data_levels = CHARACTERS_5_BIT[c]
            except KeyError:
                raise ValueError(f"character '{c}' cannot be rendered")

            for data_level in reversed(data_levels):
                data_level_map[date] = data_level
                date -= timedelta(days=1)

            for _ in range(7):
                data_level_map[date] = 0
                date -= timedelta(days=1)

        return data_level_map
