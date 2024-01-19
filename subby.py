import argparse

from srt import decodeSRTFile

ARG_HELP = {
        "input": "The input file",
        "output": "The output file",
        "delay": "Delay subtitle lines in milliseconds",
        "begin": "Line to begin delay from"}

parser = argparse.ArgumentParser(prog="subby",
        description="Subtitle editor")

# TODO add multi file support
parser.add_argument("input", help=ARG_HELP["input"])
parser.add_argument("-o", "--output", help=ARG_HELP["output"])
parser.add_argument("-d", "--delay", type=int, default=0,
        help=ARG_HELP["delay"])
parser.add_argument("-b", "--begin", default=0, type=int,
        help=ARG_HELP["begin"])

def main():
    global parser

    args = parser.parse_args()

    subs = decodeSRTFile(args.input)
    for subtitle in subs.sublines[args.begin:]:
        subtitle.duration.addDelay(args.delay)

    subs.writeToFile(args.output)

if __name__ == "__main__":
    main()
