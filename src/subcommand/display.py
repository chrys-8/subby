from typing import Any

from argparser import ARG_ENABLE, SUBCMD_INPUT_MANY, Flag, Subcommand
from filerange import FileRange
from srt import SRTDecoder, DecodeException, SRTFile, check_index_mismatch
from logger import debug, warn, error, info

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

    # TODO change to verbose
    useLongInfo: bool = args["long"]

    try:
        if args["dbg1"]:
            decoder, srtfile = dbg1_decode_utf8_only(filerange)

        else:
            # TODO add encoding flags; needs reactoring
            decoder = SRTDecoder(filerange)
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

        if useLongInfo:
            line_numbers = (str(index)
                            for index in decoder.stats.consecutive_blank_lines)

            info(f"\ton line numbers: {', '.join(line_numbers)}")

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

        if useLongInfo:
            info("Reported line number\tActual line number")
            for reported, actual in mismatches:
                info(f"{reported}\t{actual}")

    if not hasIssues:
        info("\tno issues")

    if args["missing"]:
        warn("Utility for determining missing line numbers not yet" \
                " implemented")

def display(args: dict[str, Any]) -> None:
    '''Implement display subcommand for multiple files'''
    input_count = len(args["input"])
    if input_count > 1:
        info(f"Displaying information for {input_count} files")

    for filerange in args["input"]:
        display_one(filerange, args)
        info("")

subcommand_display = Subcommand(
        name = "display",
        function = display,
        helpstring = "Display information about subtitle file",
        args = [
            Flag(
                name = "-long",
                helpstring = "Display detailed information",
                type = ARG_ENABLE),
            Flag(
                name = "-missing",
                helpstring = "Not implemented",
                type = ARG_ENABLE),
            Flag(
                name = "-dbg1",
                helpstring = "",
                type = ARG_ENABLE
                ),
            SUBCMD_INPUT_MANY
            ]
        )
