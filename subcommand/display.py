import argparse
from filerange import FileRange
from srt import SRTDecoder, DecodeException, check_index_mismatch
from argparser import SUBCMD_INPUT_MANY, Subcommand, SubcommandArgument, \
        ARG_ENABLE

def display_one(filerange: FileRange, args: argparse.Namespace) -> None:
    '''Implement display subcommand'''

    if filerange.linerange is not None or filerange.timerange is not None:
        print(f"Ignoring provided range for {filerange.filename}...")

    useLongInfo: bool = args.long

    try:
        # TODO add encoding flags; needs reactoring
        decoder = SRTDecoder(filerange)
        srtfile = decoder.decode()
    except DecodeException:
        print("Could not decode file")
        return

    srtfile.sort_subtitles()

    print(f"srt subtitles: {srtfile.filerange.filename}")
    print(f"\tcontains {len(srtfile.sublines)} lines")

    hasIssues = False

    # consecutive blank lines
    if len(decoder.stats.consecutive_blank_lines) != 0:
        cases = len(decoder.stats.consecutive_blank_lines)
        print(f"\t{cases} cases of consecutive blank lines")
        hasIssues = True

        if useLongInfo:
            line_numbers = (str(index)
                            for index in decoder.stats.consecutive_blank_lines)

            print(f"\ton line numbers: {', '.join(line_numbers)}")

    # missing terminating blank line
    if decoder.stats.missing_end_blank_line:
        print(f"\tmissing terminating blank line")
        hasIssues = True

    # index mismatches
    mismatches = check_index_mismatch(srtfile)
    if len(mismatches) != 0:
        print(f"\t{len(mismatches)} cases of mismatched line indices")
        print("\tthis might suggest missing lines")
        hasIssues = True

        if useLongInfo:
            print("Reported line number\tActual line number")
            for reported, actual in mismatches:
                print(f"{reported}\t{actual}")

    if not hasIssues:
        print("\tno issues")

    if args.missing:
        print("Utility for determining missing line numbers not yet" \
                " implemented")

def display(args: argparse.Namespace) -> None:
    '''Implement display subcommand for multiple files'''
    input_count = len(args.input)
    if input_count > 1:
        print(f"Displaying information for {input_count} files\n\n", end = "")

    for filerange in args.input:
        display_one(filerange, args)
        print("\n", end = "")

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
