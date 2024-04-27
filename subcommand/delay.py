import argparse

from logger import error, info
import stime
from srt import SRTDecoder, DecodeException
from argparser import Subcommand, SUBCMD_OUTPUT, SubcommandArgument,\
        ARG_ENABLE, SUBCMD_INPUT_SINGLE
from subcommand.common import filerange_filter_function, save_subtitle_file

def delay(args: argparse.Namespace) -> None:
    '''Implement delay for subtitle range'''

    try:
        info(f"Reading '{args.input.filename}'\n")
        srtfile = SRTDecoder(args.input).decode()
    except DecodeException:
        error("Could not decode file\n")
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

    filter_fn = filerange_filter_function(srtfile.filerange)

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

    info(f"Modified {counter} of {len(srtfile.sublines)} lines\n")

    # exclusive flags
    if args.exclusive:
        trimmed_sublines = [
                line
                for line, mask in zip(srtfile.sublines, exclusive_mask)
                if mask]

        srtfile.sublines = trimmed_sublines

    save_subtitle_file(srtfile, args)

subcommand_delay = Subcommand(
        name = "delay",
        function = delay,
        helpstring = "Delay a range of subtitles by a specified amount",
        args = [
            SUBCMD_OUTPUT,
            SubcommandArgument(
                name = "-u",
                helpstring = "Specify unit of delay (default: millisecond)",
                long_name = "--unit",
                choices = ("millisecond", "second", "minute", "ms", "s")),
            SubcommandArgument(
                name = "-x",
                helpstring = "Encode only the specified range",
                long_name = "--exclusive",
                type = ARG_ENABLE),
            SUBCMD_INPUT_SINGLE,
            SubcommandArgument(
                name = "delay",
                helpstring = "Amount of units (see -u) to delay by",
                display_name = "delay_by",
                value_type = int)
            ]
        )
