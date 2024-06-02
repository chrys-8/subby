<<<<<<< HEAD
from typing import Any

from cli import Command, Parameter, ARG_OPTIONAL
=======
import argparse
from typing import Any

#from argparser import SUBCMD_INPUT_SINGLE, SUBCMD_OUTPUT, Subcommand, SubcommandArgument, ARG_OPTIONAL
from argparser import SUBCMD_INPUT_SINGLE, SUBCMD_OUTPUT, Flag, Subcommand
>>>>>>> 3c378df0b457217c2bc8c980ec3a0c163a416c48
from filerange import FileRange, filerange
from logger import error, info
from srt import SRTDecoder, DecodeException
from subcommand.common import save_subtitle_file, filerange_filter_function,\
        single_srt_file_input_params, srt_file_output_params

def trim(args: dict[str, Any]) -> None:
    '''Implement trim subcommand for subtitle range'''
    range_provided, input_range = args["range"]
    input_: FileRange
    if range_provided:
        info(f"Using provided range: {input_range}")
        input_ = input_range
        input_.filename = args["input"].filename

    else:
        input_ = args["input"]

    try:
        info(f"Reading '{args['input'].filename}'")
        srtfile = SRTDecoder(input_).decode()
    except DecodeException:
        error("Could not decode file")
        return

    srtfile.sort_subtitles()
    filter_fn = filerange_filter_function(srtfile.filerange)
    trimmed_sublines = filter(filter_fn, srtfile.sublines)
    srtfile.sublines = list(trimmed_sublines)

    for index, subline in enumerate(srtfile.sublines):
        subline.index = index + 1 # 1-indexed

    save_subtitle_file(srtfile, args)

def parse_range(args: dict[str, Any]) -> None:
    '''Post processing to yield file range'''
    provided: bool
    input_str: str
    provided, input_str = args["range"]
    input_range = filerange(input_str)
    args["range"] = (provided, input_range)

def validate_no_range_conflict(args: dict[str, Any]) -> bool:
    '''Check whether conflicting flags have been set'''
    provided, _ = args["range"]
<<<<<<< HEAD
    if provided and args["use_ranges"]: # TODO may not work
=======
    if provided and args["use-ranges"]:
>>>>>>> 3c378df0b457217c2bc8c980ec3a0c163a416c48
        error("Cannot have conflicting ranges")
        return False

    return True

def option_range(value: str) -> tuple[bool, str]:
    '''Wrap range in a tuple to detect input conditions'''
    return (True, ":" + value)

subcommand_trim = Command(
        name = "trim",
        function = trim,
        helpstring = "Trim to specified range of lines or timestamps",
        args = [
            SUBCMD_OUTPUT,
            SUBCMD_INPUT_SINGLE,
            Flag(
                name = "range",
                helpstring = "A range of lines or timestamps",
                value_type = option_range,
                default = (False, "start-end"))
            ],
        validators = [validate_no_range_conflict],
        post_processors = [parse_range]
        )
