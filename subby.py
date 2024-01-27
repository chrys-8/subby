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

    subs = decodeSRTFile(args.input)
    for subtitle in subs.sublines[args.begin:]:
        subtitle.duration.addDelay(args.delay)

    if args.overwrite:
        subs.saveToFile()

    elif args.output is None:
        subs.print()

    else:
        subs.writeToFile(args.output)

if __name__ == "__main__":
    main()
