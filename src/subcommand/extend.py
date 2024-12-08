from re import error
from typing import Any
from cli import ARG_OPTIONAL, Command, Parameter
from logger import info, warn
from srt import DecodeException, SRTDecoder
from stime import Time
from subcommand.common import save_subtitle_file, single_srt_file_input_params, srt_file_output_params
from itertools import pairwise

# TODO move this to stime
def time_difference(begin: Time, end: Time) -> int:
    '''Return the difference in milliseconds between two Time values'''
    return end.value - begin.value

def extend(args: dict[str, Any]) -> None:
    '''Implement extend subcommand'''
    warn("The extend subcommand is experiment so remember to have backups")

    try:
        info(f"Reading '{args['input'].filename}'")
        srtfile = SRTDecoder(args["input"]).decode()
    except DecodeException:
        error("Could not decode file")
        return

    srtfile.sort_subtitles()
    extend_ms: int = args["extend"]
    gap_ms: int = args["gap"]

    for this_line, next_line in pairwise(srtfile.sublines):
        difference = time_difference(this_line.duration.end, next_line.duration.begin)
        if difference < gap_ms:
            continue

        elif difference <= extend_ms:
            this_line.duration.end.value = next_line.duration.begin.value - gap_ms

        else:
            this_line.duration.end.value += extend_ms

    save_subtitle_file(srtfile, args)

subcommand_extend = Command(
        name = "extend",
        function = extend,
        helpstring = "Extend subtitle duration",
        parameters = [
            srt_file_output_params(),
            single_srt_file_input_params(),
            Parameter(
                name = "extend",
                helpstring = "Amount of milliseconds to extend by",
                display_name = "extend_by",
                value_type = int),
            Parameter(
                name = "gap",
                helpstring = "Threshold between subtitle lines",
                display_name = "threshold",
                type = ARG_OPTIONAL,
                value_type = int,
                default = 100)
            ]
        )

