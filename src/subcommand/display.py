from typing import Any

from filerange import FileRange
from srt import SRTDecoder, DecodeException, SRTFile, check_index_mismatch
from cli import Command, Parameter, ARG_ENABLE
from logger import debug, warn, error, info, verbose
from subcommand.common import multiple_srt_file_input_params

def dbg1_decode_utf8_only(filerange: FileRange) -> tuple[SRTDecoder, SRTFile]:
    """Debug UTF8 decoding"""
    decoder = SRTDecoder(filerange)

    try:
        with open(decoder.filerange.filename, 'r',
                  encoding = decoder.encoding) as file:
            for line in file:
                line = line.strip('\n')
                decoder.filebuffer.append(line)

    except UnicodeDecodeError as err:
        debug(f"Encoding error in {filerange.filename}")
        debug(f"{err!r}")
        debug(f"Reason: {err.reason}")
        raise DecodeException

    subs = decoder.decode()
    return decoder, subs

def display_one(filerange: FileRange, args: dict[str, Any]) -> None:
    '''Implement display subcommand'''

    if filerange.linerange is not None or filerange.timerange is not None:
        warn(f"Ignoring provided range for {filerange.filename}...")

    try:
        if args["dbg1"]:
            decoder, srtfile = dbg1_decode_utf8_only(filerange)

        else:
            encoding = args["encoding"]
            decoder = SRTDecoder(filerange, encoding)
            srtfile = decoder.decode()

    except DecodeException:
        error("Could not decode file")
        return

    srtfile.sort_subtitles()

    info(f"srt subtitles: {srtfile.filerange.filename}")
    info(f"\tcontains {len(srtfile.sublines)} lines")

    hasIssues = False

    # consecutive blank lines
    if len(decoder.stats.consecutive_blank_lines) != 0:
        cases = len(decoder.stats.consecutive_blank_lines)
        info(f"\t{cases} cases of consecutive blank lines")
        hasIssues = True

        line_numbers = (str(index)
                        for index in decoder.stats.consecutive_blank_lines)

        verbose(f"\ton line numbers: {', '.join(line_numbers)}")

    # missing terminating blank line
    if decoder.stats.missing_end_blank_line:
        warn(f"\tmissing terminating blank line")
        hasIssues = True

    # index mismatches
    mismatches = check_index_mismatch(srtfile)
    if len(mismatches) != 0:
        warn(f"\t{len(mismatches)} cases of mismatched line indices")
        warn("\tthis might suggest missing lines")
        hasIssues = True

        verbose("Reported line number\tActual line number")
        for reported, actual in mismatches:
            verbose(f"{reported}\t{actual}")

    if not hasIssues:
        info("\tno issues")

def display(args: dict[str, Any]) -> None:
    '''Implement display subcommand for multiple files'''
    input_count = len(args["input"])
    if input_count > 1:
        info(f"Displaying information for {input_count} files")

    for filerange in args["input"]:
        display_one(filerange, args)
        info("")

subcommand_display = Command(
        name = "display",
        function = display,
        helpstring = "Display information about subtitle file",
        parameters = [
            Parameter(
                name = "--dbg1",
                helpstring = "",
                type = ARG_ENABLE
                ),
            multiple_srt_file_input_params()
            ]
        )
