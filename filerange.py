from dataclasses import dataclass

from stime import TimeRange, Time
from logger import warn

@dataclass
class FileRange:
    '''Represents command line representation of a range of lines in a
    subtitle file'''

    filename: str
    timerange: TimeRange | None
    linerange: tuple[int, int] | None

def to_linerange(start_: str, end_: str) -> tuple[int, int] | None:
    '''Attempts to convert input to line range'''
    strip_hash = lambda s: s[1:] if s.startswith('#') else s
    start = strip_hash(start_)
    end = strip_hash(end_)

    try:
        start = 0 if start.lower() == "start" else int(start)
        end = -1 if end.lower() == "end" else int(end)
        return start, end

    except ValueError:
        return None

def to_timerange(start_: str, end_: str) -> TimeRange | None:
    '''Attempts to convert input to time range'''
    try:
        if start_.lower() == "start":
            start = Time(0)

        else:
            start = Time.fromStr(start_)

        if end_.lower() == "end":
            end = Time(-1)

        else:
            end = Time.fromStr(end_)

        return TimeRange(start, end)

    except ValueError:
        return None

def split_filerange(value: str) -> tuple[str, str | None]:
    '''Naïvely split filerange string on last colon'''
    split = value.split(':')
    if len(split) == 1:
        # no specified range or other delimiters
        return value, None

    # use last split as range_str and join remainder
    filename = ':'.join(split[:-1])
    range_str = split[-1]
    return filename, range_str

def warn_filerange_fallback(range_str: str) -> None:
    warn(f"Cannot read range '{range_str}'; interpreting as filename\n")
    warn("WARNING: if you intended to specify a line range of timerange,"    \
            " this action may destroy data unintentionally if you have"       \
            " overwrite flag set\n")
    warn("It is recommended to only use the overwrite flag if you know what" \
            " you're doing\n")

def filerange(value: str) -> FileRange:
    '''Convert command line string to a FileRange'''
    filename, range_str = split_filerange(value)
    if range_str is None:
        return FileRange(value, None, None)

    # split at range separator
    range_str_split = tuple(range_str.split('-'))
    if len(range_str_split) != 2:
        # fallback to filename
        warn_filerange_fallback(range_str)
        return FileRange(value, None, None)

    start, end = range_str_split
    linerange = to_linerange(start, end)
    if linerange is not None:
        return FileRange(filename, None, linerange)

    timerange = to_timerange(start, end)
    if timerange is not None:
        return FileRange(filename, timerange, None)

    warn_filerange_fallback(range_str)
    return FileRange(value, None, None)
