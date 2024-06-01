from typing import Callable, Any

from filerange import FileRange
from logger import LogFormatter, error, info
from srt import SRTFile
from subtitles import SubtitleLine
import stime
import term

def in_linerange(linerange: tuple[int, int]) -> Callable[[SubtitleLine], bool]:
    '''Yield filter function for linerange'''
    start, end = linerange
    if start == 0 and end == -1:
        return lambda _: True
    elif end == -1:
        return lambda line: start <= line.index
    else:
        return lambda line: start <= line.index and line.index < end

def in_timerange(timerange: stime.TimeRange) -> Callable[[SubtitleLine], bool]:
    '''Yield filter function for linerange'''
    if timerange.end.value == -1:
        return lambda line: timerange.begin.value <= line.duration.begin.value
    else:
        return lambda line: timerange.time_in_range(line.duration.begin)

def filerange_filter_function(filerange: FileRange) \
        -> Callable[[SubtitleLine], bool]:
    '''Yield filter function specified for filerange'''
    if filerange.linerange is not None:
        return in_linerange(filerange.linerange)

    elif filerange.timerange is not None:
        return in_timerange(filerange.timerange)

    else:
        return lambda _: True

def save_subtitle_file(file: SRTFile, args: dict[str, Any]) -> None:
    '''Save subtitle file to specified filename'''
    write_success: bool
    filename: str
    if args["overwrite"]:
        filename = file.filerange.filename
        info(f"Overwriting '{filename}' with {len(file.sublines)} lines")
        write_success = file.save_to_file()

    else:
        filename = args["output"]
        info(f"Writing {len(file.sublines)} lines to '{filename}'")
        write_success = file.write_to_file(filename)

    use_term_colors: bool = False
    log_formatter: LogFormatter | None = args.get("log_formatter")
    if log_formatter is not None:
        use_term_colors = log_formatter.flags.use_term_colors

    if write_success and use_term_colors:
        prefix = term.term_color_fg("green")
        postfix = term.term_color_fg("default")
        info(f"{prefix}Finished!{postfix}")

    elif write_success:
        info("Finished!")

    else:
        error(f"Fatal error: could not save file '{filename}'")
