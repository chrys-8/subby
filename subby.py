from argparser import Commands
from srt import decodeSRTFile

def main():
    args = Commands().parse_args()

    if args is None:
        return

    subs = decodeSRTFile(args.input)
    if subs is None:
        print(f"Could not decode input: {args.input}")
        print("Perhaps the subtitle file is empty")
        return

    for subtitle in subs.sublines[args.begin:]:
        subtitle.duration.addDelay(args.delay)

    if args.overwrite:
        subs.saveToFile()

    else:
        subs.writeToFile(args.output)

if __name__ == "__main__":
    main()
