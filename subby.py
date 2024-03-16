import argparse

from srt import decodeSRTFile

ARG_HELP = {
        "input":     "The input file",
        "output":    "The output file",
        "delay":     "Delay subtitle lines in milliseconds",
        "begin":     "Line to begin delay from",
        "overwrite": "Flag to specify overwriting the input file;" \
            " ignores -o"}

parser = argparse.ArgumentParser(prog="subby",
        description="Subtitle editor")

# TODO add function for duduplicating argument name and help string
# TODO add multi file support
parser.add_argument("input", help=ARG_HELP["input"])
parser.add_argument("-o", "--output", nargs="?",
        help=ARG_HELP["output"])
parser.add_argument("-d", "--delay", type=int, default=0,
        help=ARG_HELP["delay"])
parser.add_argument("-b", "--begin", default=0, type=int,
        help=ARG_HELP["begin"])
parser.add_argument("--overwrite", action="store_true",
        help=ARG_HELP["overwrite"])

def main():
    global parser

    args = parser.parse_args()

    # TODO detect filetype; reject non-SRT

    # TODO implement force
    if not args.input.endswith(".srt"):
        print(f"'{args.input}' is not an srt file (--force (not implemented))")
        return

    if args.output is None and not args.overwrite:
        print("Please specify an output file with -o, or use the --overwrite flag")
        return

    subs = decodeSRTFile(args.input)
    if subs is None:
        return

    for subtitle in subs.sublines[args.begin:]:
        subtitle.duration.addDelay(args.delay)

    if args.overwrite:
        subs.saveToFile()

    else:
        subs.writeToFile(args.output)

if __name__ == "__main__":
    main()
