#!/usr/bin/env python3
from argparse import ArgumentParser
from enum import Enum
import re
import sys


class DataLevel(str, Enum):
    LEVEL_0 = " "
    LEVEL_1 = "-"
    LEVEL_2 = "="
    LEVEL_3 = "H"
    LEVEL_4 = "#"

    def __int__(self) -> int:
        match self:
            case DataLevel.LEVEL_0:
                return 0
            case DataLevel.LEVEL_1:
                return 1
            case DataLevel.LEVEL_2:
                return 2
            case DataLevel.LEVEL_3:
                return 3
            case DataLevel.LEVEL_4:
                return 4
            case _:
                raise ValueError("invalid DataLevel")


def parse_args():
    parser = ArgumentParser(prog="generate",
                            description="generate a DataLevelMap from a human readable representation")
    parser.add_argument("--oneline", action="store_true", help="print the resulting python tuple in one line rather than multiple")
    parser.add_argument(dest="source", nargs="?", help="the human readable representation source for the generated code", type=str)

    if len(sys.argv) == 1:
        print("missing required source value")
        parser.print_usage()
        sys.exit(1)

    return parser.parse_args()


def display_data_level(data_level: tuple[int], oneline: bool):
    string_builder = f"({', '.join(str(n) for n in data_level)})"

    if oneline:
        print(string_builder)
        return

    newlines = list(m.start() for m in re.finditer(",", string_builder))[6::7]

    for offset, i in enumerate(newlines):
        string_builder = string_builder[:offset + i + 1:] + "\n" + string_builder[offset + i + 1::]
    print(string_builder)


def main():
    namespace = parse_args()

    source: str = namespace.source
    source_lines = source.splitlines()

    if len(source_lines) > 7:
        print("source cannot contain more than 7 lines")
        return

    linear = "".join("".join(week) for week in zip(*source_lines))
    mapped = tuple(map(lambda s: int(DataLevel(s)), linear))

    display_data_level(mapped, namespace.oneline)


if __name__ == "__main__":
    main()
