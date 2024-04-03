from dataclasses import dataclass

from stime import TimeRange, Time

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

def filerange(value: str) -> FileRange:
    '''Convert command line string to a FileRange'''
    value_split = tuple(value.split(':', 1))

    # no range
    if len(value_split) == 1:
        return FileRange(value, None, None)

    filename, range_str = value_split

    # split at range separator
    range_str_split = tuple(range_str.split('-'))
    if len(range_str_split) != 2:
        print(f"Range '{range_str}' needs to be formatted as" \
                " hh:mm:ss,mmm-hh:mm:ss,mmm or #n-#n")
        raise ValueError

    start, end = range_str_split
    linerange = to_linerange(start, end)
    if linerange is not None:
        return FileRange(filename, None, linerange)

    timerange = to_timerange(start, end)
    if timerange is not None:
        return FileRange(filename, timerange, None)

    print(f"Unknown range: '{range_str}'")
    raise ValueError
