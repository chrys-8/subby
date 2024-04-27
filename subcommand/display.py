import argparse

from filerange import FileRange
from srt import SRTDecoder, DecodeException, check_index_mismatch
from argparser import SUBCMD_INPUT_MANY, Subcommand, SubcommandArgument, \
        ARG_ENABLE
from logger import warn, error, info

def display_one(filerange: FileRange, args: argparse.Namespace) -> None:
    '''Implement display subcommand'''

    if filerange.linerange is not None or filerange.timerange is not None:
        warn(f"Ignoring provided range for {filerange.filename}...\n")

    useLongInfo: bool = args.long

    try:
        # TODO add encoding flags; needs reactoring
        decoder = SRTDecoder(filerange)
        srtfile = decoder.decode()
    except DecodeException:
        error("Could not decode file\n")
        return

    srtfile.sort_subtitles()

    info(f"srt subtitles: {srtfile.filerange.filename}\n")
    info(f"\tcontains {len(srtfile.sublines)} lines\n")

    hasIssues = False

    # consecutive blank lines
    if len(decoder.stats.consecutive_blank_lines) != 0:
        cases = len(decoder.stats.consecutive_blank_lines)
        info(f"\t{cases} cases of consecutive blank lines\n")
        hasIssues = True

        if useLongInfo:
            line_numbers = (str(index)
                            for index in decoder.stats.consecutive_blank_lines)

            info(f"\ton line numbers: {', '.join(line_numbers)}\n")

    # missing terminating blank line
    if decoder.stats.missing_end_blank_line:
        warn(f"\tmissing terminating blank line\n")
        hasIssues = True

    # index mismatches
    mismatches = check_index_mismatch(srtfile)
    if len(mismatches) != 0:
        warn(f"\t{len(mismatches)} cases of mismatched line indices\n")
        warn("\tthis might suggest missing lines\n")
        hasIssues = True

        if useLongInfo:
            info("Reported line number\tActual line number\n")
            for reported, actual in mismatches:
                info(f"{reported}\t{actual}\n")

    if not hasIssues:
        info("\tno issues\n")

    if args.missing:
        warn("Utility for determining missing line numbers not yet" \
                " implemented\n")

def display(args: argparse.Namespace) -> None:
    '''Implement display subcommand for multiple files'''
    input_count = len(args.input)
    if input_count > 1:
        info(f"Displaying information for {input_count} files\n\n")

    for filerange in args.input:
        display_one(filerange, args)
        info("\n")

subcommand_display = Subcommand(
        name = "display",
        function = display,
        helpstring = "Display information about subtitle file",
        args = [
            SubcommandArgument(
                name = "--long",
                helpstring = "Display detailed information",
                type = ARG_ENABLE),
            SubcommandArgument(
                name = "--missing",
                helpstring = "Not implemented",
                type = ARG_ENABLE),
            SUBCMD_INPUT_MANY
            ]
        )
