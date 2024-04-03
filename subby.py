from typing import Callable
from argparser import Commands
from srt import DecodeException, SRTDecoder, check_index_mismatch
import stime

import argparse

from subtitles import SubtitleLine

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

def delay(args: argparse.Namespace) -> None:
    '''Implement delay for subtitle range'''

    try:
        print(f"Reading '{args.input.filename}'")
        srtfile = SRTDecoder(args.input).decode()
    except DecodeException:
        print("Could not decode file")
        return

    srtfile.sort_subtitles()

    # final delay in milliseconds
    delay: int
    if args.unit == "minute":
        delay = args.delay * stime.MINUTES

    elif args.unit in ("second", "s"):
        delay = args.delay * stime.SECONDS

    else:
        delay = args.delay

    # filter function for range type
    filter_fn: Callable[[SubtitleLine], bool]
    if srtfile.filerange.linerange is not None:
        filter_fn = in_linerange(srtfile.filerange.linerange)

    elif srtfile.filerange.timerange is not None:
        filter_fn = in_timerange(srtfile.filerange.timerange)

    else:
        filter_fn = lambda _: True

    exclusive_mask: list[bool] = []
    counter = 0
    # add delay to filtered lines
    for line in srtfile.sublines:
        if filter_fn(line):
            exclusive_mask.append(True)
            line.duration.add_delay(delay)
            counter = counter + 1

        else:
            exclusive_mask.append(False)

    print(f"Modified {counter} of {len(srtfile.sublines)} lines")

    # exclusive flags
    if args.exclusive:
        trimmed_sublines = [
                line
                for line, mask in zip(srtfile.sublines, exclusive_mask)
                if mask]

        srtfile.sublines = trimmed_sublines

    # encode and save
    write_success: bool
    filename: str
    if args.overwrite:
        filename = srtfile.filerange.filename
        print(f"Overwriting '{filename}' with {len(srtfile.sublines)} lines")
        write_success = srtfile.save_to_file()

    else:
        filename = args.output
        print(f"Writing {len(srtfile.sublines)} lines to '{filename}'")
        write_success = srtfile.write_to_file(filename)

    if write_success:
        print("Finished!")

    else:
        print(f"Fatal error: could not save to file '{filename}'")

def main() -> None:
    args = Commands().parse_args()

    if args is None:
        # assume error was provided by validators in Commands
        return

    if args.subcmd is None:
        print("Interactive mode coming soon! For now, use -h for help.")

    elif args.subcmd == "delay":
        delay(args)

    return

if __name__ == "__main__":
    main()
